"""Analytics endpoints: summary, products, monthly, day-of-month."""
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.auth import get_current_user
from app.database import get_db
from app.schemas import (
    SummaryOut, ProductRow, MonthlyRow, DayRow, AnalyticsStatusOut
)

router = APIRouter()


async def _get_analytics(upload_id: str, owner_id: str):
    """Fetch analytics result, enforcing ownership on both upload and analytics."""
    db = get_db()

    # Verify upload ownership
    upload = await db.uploads.find_one({"_id": ObjectId(upload_id), "owner_id": owner_id})
    if not upload:
        raise HTTPException(404, "Upload not found")

    result = await db.analytics_results.find_one(
        {"owner_id": owner_id, "upload_id": upload_id}
    )
    if not result:
        raise HTTPException(404, "Analytics not yet available for this upload")
    if result.get("status") == "error":
        raise HTTPException(500, f"Analytics processing failed: {result.get('error', 'Unknown error')}")

    return result.get("data", {})


@router.get("/{upload_id}/summary", response_model=SummaryOut)
async def get_summary(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _get_analytics(upload_id, str(current_user["_id"]))
    s = data.get("summary", {})
    products = data.get("products", [])
    monthly = data.get("monthly", [])

    best_product = products[0]["product_name"] if products else None
    best_month = max(monthly, key=lambda m: m["revenue"])["month"] if monthly else None

    return SummaryOut(
        total_revenue=s.get("total_revenue", 0.0),
        total_units=s.get("total_units", 0),
        product_count=s.get("product_count", 0),
        order_count=s.get("order_count", 0),
        row_count=s.get("row_count", 0),
        best_product=best_product,
        best_month=best_month,
    )


@router.get("/{upload_id}/products", response_model=list[ProductRow])
async def get_products(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _get_analytics(upload_id, str(current_user["_id"]))
    return [
        ProductRow(
            rank=p["rank"],
            product_name=p["product_name"],
            total_revenue=p["total_revenue"],
            total_quantity=p["total_quantity"],
            category=p.get("category") or None,
        )
        for p in data.get("products", [])
    ]


@router.get("/{upload_id}/monthly", response_model=list[MonthlyRow])
async def get_monthly(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _get_analytics(upload_id, str(current_user["_id"]))
    return [
        MonthlyRow(month=m["month"], revenue=m["revenue"], units_sold=m["units_sold"])
        for m in data.get("monthly", [])
    ]


@router.get("/{upload_id}/day-of-month", response_model=list[DayRow])
async def get_day_of_month(upload_id: str, current_user: dict = Depends(get_current_user)):
    data = await _get_analytics(upload_id, str(current_user["_id"]))
    return [
        DayRow(day=d["day"], revenue=d["revenue"], units_sold=d["units_sold"])
        for d in data.get("day_of_month", [])
    ]


@router.post("/{upload_id}/process", response_model=AnalyticsStatusOut)
async def reprocess(upload_id: str, current_user: dict = Depends(get_current_user)):
    """Re-run Spark analytics for an existing upload."""
    db = get_db()
    owner_id = str(current_user["_id"])

    upload = await db.uploads.find_one({"_id": ObjectId(upload_id), "owner_id": owner_id})
    if not upload:
        raise HTTPException(404, "Upload not found")

    from app.spark_runner import run_spark_job
    from datetime import datetime, timezone

    cursor = db.sales_records.find({"owner_id": owner_id, "upload_id": upload_id})
    records = await cursor.to_list(length=None)

    if not records:
        raise HTTPException(400, "No records found for this upload")

    try:
        analytics = run_spark_job(records, f"job-{upload_id}-retry")
        await db.analytics_results.update_one(
            {"owner_id": owner_id, "upload_id": upload_id},
            {"$set": {
                "status": "success",
                "processed_at": datetime.now(timezone.utc),
                "data": analytics,
                "error": None,
            }},
            upsert=True,
        )
        await db.uploads.update_one(
            {"_id": ObjectId(upload_id)},
            {"$set": {"status": "ready"}},
        )
        return AnalyticsStatusOut(upload_id=upload_id, status="success",
                                  processed_at=datetime.now(timezone.utc))
    except Exception as e:
        return AnalyticsStatusOut(upload_id=upload_id, status="error", error=str(e)[:500])
