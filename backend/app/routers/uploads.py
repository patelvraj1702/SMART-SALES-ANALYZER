"""Upload endpoints: preview, confirm, list, get, delete."""
import io
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import json

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.file_parser import compute_fingerprint, normalise_and_validate, read_file
from app.schemas import (
    ColumnMapping,
    ConfirmUploadRequest,
    UploadOut,
    UploadPreviewResponse,
)
from app.spark_runner import run_spark_job

router = APIRouter()

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024
PREVIEW_ROWS = 10


def _upload_to_out(doc: dict) -> UploadOut:
    return UploadOut(
        id=str(doc["_id"]),
        filename=doc["filename"],
        created_at=doc["created_at"],
        status=doc["status"],
        total_rows=doc.get("total_rows", 0),
        accepted_rows=doc.get("accepted_rows", 0),
        rejected_rows=doc.get("rejected_rows", 0),
        validation_summary=doc.get("validation_summary"),
        error_summary=doc.get("error_summary"),
    )


@router.post("/preview", response_model=UploadPreviewResponse)
async def preview_upload(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, f"File too large. Maximum is {settings.MAX_FILE_SIZE_MB} MB.")

    try:
        df = read_file(content, file.filename or "upload.csv")
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    if len(df) == 0:
        raise HTTPException(400, "File is empty.")

    fingerprint = compute_fingerprint(content)

    columns = [str(c) for c in df.columns]
    sample = []
    for row in df.head(PREVIEW_ROWS).to_dict(orient="records"):
        clean_row = {}
        for k, v in row.items():
            try:
                is_na = pd.isna(v)
            except (TypeError, ValueError):
                is_na = False
            if is_na:
                clean_row[str(k)] = None
            elif hasattr(v, "strftime"):
                clean_row[str(k)] = v.strftime("%Y-%m-%d")
            else:
                clean_row[str(k)] = v
        sample.append(clean_row)

    from app.date_utils import analyze_columns_temporal
    temporal_analysis = analyze_columns_temporal(df)

    return UploadPreviewResponse(
        columns=columns,
        sample_rows=sample,
        row_count=len(df),
        fingerprint=fingerprint,
        temporal_analysis=temporal_analysis,
    )


@router.post("", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
async def confirm_upload(
    file: UploadFile = File(...),
    mapping_json: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Re-read the file, validate rows, store records, run Spark analytics."""
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, f"File too large. Maximum is {settings.MAX_FILE_SIZE_MB} MB.")

    try:
        body = ConfirmUploadRequest.model_validate_json(
            json.dumps({"filename": file.filename, "fingerprint": "", "column_mapping": json.loads(mapping_json)})
        )
    except Exception as e:
        raise HTTPException(422, f"Invalid mapping: {e}")

    mapping: ColumnMapping = body.column_mapping

    try:
        df = read_file(content, file.filename or "upload.csv")
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    if len(df) > settings.MAX_ROWS:
        raise HTTPException(400, f"File has too many rows. Maximum is {settings.MAX_ROWS}.")

    fingerprint = compute_fingerprint(content)
    owner_id = str(current_user["_id"])
    db = get_db()

    # Duplicate fingerprint check for this user
    existing = await db.uploads.find_one({"owner_id": owner_id, "fingerprint": fingerprint})
    if existing:
        raise HTTPException(409, "This file has already been uploaded (duplicate detected).")

    # Normalise and validate
    accepted, rejected = normalise_and_validate(df, mapping)
    total_rows = len(df)
    accepted_rows = len(accepted)
    rejected_rows = len(rejected)

    upload_id = str(uuid.uuid4())

    upload_doc = {
        "_id": ObjectId(),
        "upload_id": upload_id,
        "owner_id": owner_id,
        "filename": file.filename or "upload",
        "fingerprint": fingerprint,
        "created_at": datetime.now(timezone.utc),
        "status": "processing",
        "total_rows": total_rows,
        "accepted_rows": accepted_rows,
        "rejected_rows": rejected_rows,
        "validation_summary": {
            "rejected_sample": rejected[:20]
        },
    }
    await db.uploads.insert_one(upload_doc)
    mongo_id = str(upload_doc["_id"])

    if accepted_rows == 0:
        await db.uploads.update_one(
            {"_id": upload_doc["_id"]},
            {"$set": {"status": "failed", "error_summary": "No valid rows after validation"}},
        )
        upload_doc["status"] = "failed"
        upload_doc["error_summary"] = "No valid rows after validation"
        return _upload_to_out(upload_doc)

    # Insert sales records
    records_to_insert = [
        {**rec, "owner_id": owner_id, "upload_id": mongo_id}
        for rec in accepted
    ]
    await db.sales_records.insert_many(records_to_insert)

    # Run Spark analytics (synchronous for small college dataset)
    try:
        analytics = run_spark_job(accepted, f"job-{mongo_id}")
        await db.analytics_results.update_one(
            {"owner_id": owner_id, "upload_id": mongo_id},
            {"$set": {
                "owner_id": owner_id,
                "upload_id": mongo_id,
                "status": "success",
                "processed_at": datetime.now(timezone.utc),
                "data": analytics,
            }},
            upsert=True,
        )
        await db.uploads.update_one(
            {"_id": upload_doc["_id"]},
            {"$set": {"status": "ready"}},
        )
        upload_doc["status"] = "ready"
    except Exception as e:
        err = str(e)[:500]
        await db.analytics_results.update_one(
            {"owner_id": owner_id, "upload_id": mongo_id},
            {"$set": {
                "owner_id": owner_id,
                "upload_id": mongo_id,
                "status": "error",
                "error": err,
                "processed_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        await db.uploads.update_one(
            {"_id": upload_doc["_id"]},
            {"$set": {"status": "spark_error", "error_summary": err}},
        )
        upload_doc["status"] = "spark_error"
        upload_doc["error_summary"] = err

    return _upload_to_out(upload_doc)


@router.get("", response_model=list[UploadOut])
async def list_uploads(current_user: dict = Depends(get_current_user)):
    db = get_db()
    owner_id = str(current_user["_id"])
    cursor = db.uploads.find({"owner_id": owner_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [_upload_to_out(d) for d in docs]


@router.get("/{upload_id}", response_model=UploadOut)
async def get_upload(upload_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    owner_id = str(current_user["_id"])
    doc = await db.uploads.find_one({"_id": ObjectId(upload_id), "owner_id": owner_id})
    if not doc:
        raise HTTPException(404, "Upload not found")
    return _upload_to_out(doc)


@router.delete("/{upload_id}", status_code=204)
async def delete_upload(upload_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    owner_id = str(current_user["_id"])

    doc = await db.uploads.find_one({"_id": ObjectId(upload_id), "owner_id": owner_id})
    if not doc:
        raise HTTPException(404, "Upload not found")

    mongo_id = str(doc["_id"])
    await db.uploads.delete_one({"_id": doc["_id"]})
    await db.sales_records.delete_many({"owner_id": owner_id, "upload_id": mongo_id})
    await db.analytics_results.delete_one({"owner_id": owner_id, "upload_id": mongo_id})
