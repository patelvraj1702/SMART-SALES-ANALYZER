"""Export endpoints: download analytics results as CSV files."""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId

from app.auth import get_current_user
from app.database import get_db

router = APIRouter()


async def _fetch_analytics_data(upload_id: str, owner_id: str) -> dict:
    db = get_db()
    upload = await db.uploads.find_one({"_id": ObjectId(upload_id), "owner_id": owner_id})
    if not upload:
        raise HTTPException(404, "Upload not found")

    result = await db.analytics_results.find_one(
        {"owner_id": owner_id, "upload_id": upload_id}
    )
    if not result or result.get("status") != "success":
        raise HTTPException(404, "Analytics not ready for export")

    return result.get("data", {})


def _make_csv_response(rows: list[dict], fieldnames: list[str], filename: str) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{upload_id}/products.csv")
async def export_products(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _fetch_analytics_data(upload_id, str(current_user["_id"]))
    rows = data.get("products", [])
    return _make_csv_response(
        rows,
        fieldnames=["rank", "product_name", "total_revenue", "total_quantity", "category"],
        filename="product_rankings.csv",
    )


@router.get("/{upload_id}/monthly.csv")
async def export_monthly(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _fetch_analytics_data(upload_id, str(current_user["_id"]))
    rows = data.get("monthly", [])
    return _make_csv_response(
        rows,
        fieldnames=["month", "revenue", "units_sold"],
        filename="monthly_analytics.csv",
    )


@router.get("/{upload_id}/day-of-month.csv")
async def export_day_of_month(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _fetch_analytics_data(upload_id, str(current_user["_id"]))
    rows = data.get("day_of_month", [])
    return _make_csv_response(
        rows,
        fieldnames=["day", "revenue", "units_sold"],
        filename="day_of_month_analytics.csv",
    )
