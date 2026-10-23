"""Reprocess grocery_shop_sales_full_year_2026.xlsx with date engine and run Spark."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
from bson import ObjectId
import motor.motor_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.file_parser import read_file, normalise_and_validate
from app.schemas import ColumnMapping
from app.spark_runner import run_spark_job


async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    print(f"Connected to MongoDB: {db.name}")

    # 1. Locate upload
    upload = await db.uploads.find_one({"filename": "grocery_shop_sales_full_year_2026.xlsx"})
    if not upload:
        print("Upload grocery_shop_sales_full_year_2026.xlsx not found, listing recent uploads:")
        async for u in db.uploads.find():
            print(" -", u["_id"], u["filename"], u.get("total_rows"))
        return

    upload_id = str(upload["_id"])
    owner_id = str(upload.get("owner_id"))
    print(f"Found upload: ID={upload_id}, owner_id={owner_id}, filename={upload['filename']}, total_rows={upload.get('total_rows')}")

    # 2. Check source file
    file_path = Path(r"C:\Users\patel\Downloads\grocery_shop_sales_full_year_2026.xlsx")
    if not file_path.exists():
        print(f"File not found at {file_path}")
        return

    with open(file_path, "rb") as f:
        content = f.read()

    df = read_file(content, file_path.name)
    print(f"Read DataFrame shape: {df.shape}, Columns: {list(df.columns)}")

    # 3. Normalise and validate
    mapping = ColumnMapping(
        product_name="product_name",
        quantity="quantity",
        unit_price="unit_price",
        line_total="line_total",
        transaction_date="transaction_date",
        transaction_time=None,
        category="category" if "category" in df.columns else None,
        order_id="order_id" if "order_id" in df.columns else None,
        date_format_pref="auto",
    )

    accepted, rejected = normalise_and_validate(df, mapping)
    print(f"Validation complete: accepted={len(accepted)}, rejected={len(rejected)}")
    if accepted:
        print("Sample accepted record:", accepted[0])

    # 4. Update sales_records in DB
    print("Deleting old sales_records for this upload...")
    del_res = await db.sales_records.delete_many({"upload_id": upload_id})
    print(f"Deleted {del_res.deleted_count} old sales records.")

    records_to_insert = [
        {**r, "owner_id": owner_id, "upload_id": upload_id}
        for r in accepted
    ]

    # Insert in batches of 5000 to keep motor efficient
    batch_size = 5000
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        await db.sales_records.insert_many(batch)
    print(f"Inserted {len(records_to_insert)} sales records into DB.")

    # 5. Run Scala Spark job
    print(f"Running Spark job for {len(accepted)} records...")
    spark_analytics = run_spark_job(accepted, f"job-{upload_id}")
    print("Spark job finished!")
    print("Spark analytics keys:", list(spark_analytics.keys()))

    monthly = spark_analytics.get("monthly", [])
    print(f"Monthly buckets count: {len(monthly)}")
    for m in monthly:
        print(f"  {m.get('month')}: revenue=${m.get('revenue', 0):,.2f}, units={m.get('units_sold', 0)}")

    dom = spark_analytics.get("day_of_month", [])
    print(f"Day-of-month buckets count: {len(dom)}")

    # 6. Save analytics in MongoDB matching backend schema
    await db.analytics_results.update_one(
        {"owner_id": owner_id, "upload_id": upload_id},
        {"$set": {
            "owner_id": owner_id,
            "upload_id": upload_id,
            "status": "success",
            "processed_at": datetime.now(timezone.utc),
            "data": spark_analytics,
            "error": None,
        }},
        upsert=True
    )

    await db.uploads.update_one(
        {"_id": ObjectId(upload_id)},
        {
            "$set": {
                "status": "ready",
                "accepted_rows": len(accepted),
                "rejected_rows": len(rejected),
                "total_rows": len(df),
                "error_summary": None,
            }
        }
    )

    print("Reprocessing completed successfully!")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
