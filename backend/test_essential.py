"""
Essential Integration Test Suite for Smart Sales Analyzer
Validates all requirements from section 11 of the specification:
1. Backend health & startup
2. User registration and login
3. Rejection of unauthenticated requests
4. CSV upload and validation
5. Excel .xlsx upload and validation
6. Real Scala Spark job execution against sample data
7. Correct product ranking and revenue calculations
8. Correct monthly and day-of-month aggregations
9. Authenticated CSV exports
10. Account isolation between two users (reads, deletes, analytics, exports)
11. Safe deletion and cleanup
"""
import io
import json
import os
import sys
import uuid
import pandas as pd
from datetime import datetime
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app

client = TestClient(app)

PASS = "[PASS]"
FAIL = "[FAIL]"

def run_tests():
    print("=" * 60)
    print("STARTING ESSENTIAL TEST SUITE: SMART SALES ANALYZER")
    print("=" * 60)
    
    test_results = []
    
    def record(name, passed, detail=""):
        status = PASS if passed else FAIL
        print(f"{status} {name}: {detail}")
        test_results.append((name, passed, detail))
        if not passed:
            print(f"FAILED: {name}")

    # 1. Health check
    try:
        r = client.get("/api/health")
        record("1. Backend Health Check", r.status_code == 200, f"Status: {r.status_code}, Body: {r.json()}")
    except Exception as e:
        record("1. Backend Health Check", False, str(e))

    # Unique test emails to prevent conflict with existing data
    uid = uuid.uuid4().hex[:6]
    user1_email = f"alice_{uid}@example.com"
    user2_email = f"bob_{uid}@example.com"
    password = "TestPassword123!"

    # 2. User 1 Registration
    token1 = None
    try:
        r = client.post("/api/auth/signup", json={
            "name": "Alice Store Owner",
            "email": user1_email,
            "password": password,
            "confirm_password": password
        })
        signup_ok = r.status_code == 201
        token1 = r.json().get("access_token")
        record("2. User 1 Registration", signup_ok, f"Status {r.status_code}, Token generated: {bool(token1)}")
    except Exception as e:
        record("2. User 1 Registration", False, str(e))

    # 3. User 1 Login
    try:
        r = client.post("/api/auth/login", json={
            "email": user1_email,
            "password": password
        })
        login_ok = r.status_code == 200 and "access_token" in r.json()
        token1 = r.json().get("access_token")
        record("3. User 1 Login", login_ok, f"Status {r.status_code}")
    except Exception as e:
        record("3. User 1 Login", False, str(e))

    # 4. User 2 Registration (Isolation Target)
    token2 = None
    try:
        r = client.post("/api/auth/signup", json={
            "name": "Bob Competing Store",
            "email": user2_email,
            "password": password,
            "confirm_password": password
        })
        token2 = r.json().get("access_token")
        record("4. User 2 Registration (Isolation Target)", r.status_code == 201, f"Status {r.status_code}")
    except Exception as e:
        record("4. User 2 Registration (Isolation Target)", False, str(e))

    # 5. Rejection of unauthenticated requests
    try:
        r = client.get("/api/uploads")
        record("5. Rejection of Unauthenticated Requests", r.status_code == 401 or r.status_code == 403, f"Status {r.status_code}")
    except Exception as e:
        record("5. Rejection of Unauthenticated Requests", False, str(e))

    # 6. CSV Upload & Validation with Spark Execution
    upload1_id = None
    sample_csv_path = Path(__file__).resolve().parent.parent / "sample-data" / "sales_sample.csv"
    mapping = {
        "product_name": "product_name",
        "quantity": "quantity",
        "unit_price": "unit_price",
        "transaction_date": "transaction_date",
        "category": "category",
        "order_id": "order_id"
    }

    try:
        with open(sample_csv_path, "rb") as f:
            files = {"file": ("sales_sample.csv", f.read(), "text/csv")}
            data = {"mapping_json": json.dumps(mapping)}
            headers1 = {"Authorization": f"Bearer {token1}"}
            r = client.post("/api/uploads", files=files, data=data, headers=headers1)
        
        upload_data = r.json()
        upload1_id = upload_data.get("id")
        upload_status = upload_data.get("status")
        record(
            "6. CSV Upload & Spark Processing",
            r.status_code == 201 and upload_status == "ready",
            f"Upload ID: {upload1_id}, Status: {upload_status}, Accepted rows: {upload_data.get('accepted_rows')}"
        )
    except Exception as e:
        record("6. CSV Upload & Spark Processing", False, str(e))

    # 7. Verify Summary Metrics and Revenue Accuracy
    try:
        headers1 = {"Authorization": f"Bearer {token1}"}
        r = client.get(f"/api/analytics/{upload1_id}/summary", headers=headers1)
        s = r.json()
        expected_units = 351
        expected_revenue = 6106.49
        calc_ok = (
            r.status_code == 200 and
            s.get("total_units") == expected_units and
            abs(s.get("total_revenue", 0) - expected_revenue) < 0.1
        )
        record(
            "7. Summary Metrics & Revenue Accuracy",
            calc_ok,
            f"Revenue: {s.get('total_revenue')}, Units: {s.get('total_units')}, Best Product: {s.get('best_product')}"
        )
    except Exception as e:
        record("7. Summary Metrics & Revenue Accuracy", False, str(e))

    # 8. Verify Product Analytics & Rankings
    try:
        r = client.get(f"/api/analytics/{upload1_id}/products", headers=headers1)
        prods = r.json()
        top_prod = prods[0] if prods else {}
        prod_ok = (
            r.status_code == 200 and
            len(prods) == 7 and
            top_prod.get("product_name") == "Mechanical Keyboard" and
            top_prod.get("rank") == 1
        )
        record(
            "8. Product Analytics & Ranking",
            prod_ok,
            f"Count: {len(prods)}, Top: {top_prod.get('product_name')} (${top_prod.get('total_revenue')})"
        )
    except Exception as e:
        record("8. Product Analytics & Ranking", False, str(e))

    # 9. Verify Monthly and Day-of-Month Analytics
    try:
        r_month = client.get(f"/api/analytics/{upload1_id}/monthly", headers=headers1)
        r_day = client.get(f"/api/analytics/{upload1_id}/day-of-month", headers=headers1)
        month_data = r_month.json()
        day_data = r_day.json()
        time_ok = (
            r_month.status_code == 200 and
            r_day.status_code == 200 and
            len(month_data) == 6 and
            len(day_data) > 0
        )
        record(
            "9. Time Analytics (Monthly & Day-of-Month)",
            time_ok,
            f"Months count: {len(month_data)}, Days count: {len(day_data)}"
        )
    except Exception as e:
        record("9. Time Analytics (Monthly & Day-of-Month)", False, str(e))

    # 10. Authenticated CSV Exports
    try:
        r_exp_prod = client.get(f"/api/exports/{upload1_id}/products.csv", headers=headers1)
        r_exp_mon = client.get(f"/api/exports/{upload1_id}/monthly.csv", headers=headers1)
        r_exp_day = client.get(f"/api/exports/{upload1_id}/day-of-month.csv", headers=headers1)
        exp_ok = (
            r_exp_prod.status_code == 200 and
            r_exp_mon.status_code == 200 and
            r_exp_day.status_code == 200 and
            "product_name" in r_exp_prod.text and
            "revenue" in r_exp_mon.text
        )
        record(
            "10. CSV Exports Download",
            exp_ok,
            f"Products CSV length: {len(r_exp_prod.text)} bytes, Monthly CSV length: {len(r_exp_mon.text)} bytes"
        )
    except Exception as e:
        record("10. CSV Exports Download", False, str(e))

    # 11. Excel (.xlsx) Upload & Spark Processing
    try:
        df_csv = pd.read_csv(sample_csv_path)
        xlsx_buf = io.BytesIO()
        df_csv.to_excel(xlsx_buf, index=False)
        xlsx_bytes = xlsx_buf.getvalue()

        files = {"file": ("sales_sample.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"mapping_json": json.dumps(mapping)}
        r_xlsx = client.post("/api/uploads", files=files, data=data, headers=headers1)
        
        xlsx_data = r_xlsx.json()
        xlsx_ok = r_xlsx.status_code == 201 and xlsx_data.get("status") == "ready"
        record(
            "11. Excel (.xlsx) Upload & Spark Processing",
            xlsx_ok,
            f"Status: {r_xlsx.status_code}, Status field: {xlsx_data.get('status')}"
        )
    except Exception as e:
        record("11. Excel (.xlsx) Upload & Spark Processing", False, str(e))

    # 12. Account Isolation Verification (User 2 attempts to access User 1's data)
    try:
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 2 tries to GET User 1's upload
        r_iso_get = client.get(f"/api/uploads/{upload1_id}", headers=headers2)
        # User 2 tries to GET User 1's summary
        r_iso_sum = client.get(f"/api/analytics/{upload1_id}/summary", headers=headers2)
        # User 2 tries to GET User 1's export
        r_iso_exp = client.get(f"/api/exports/{upload1_id}/products.csv", headers=headers2)
        # User 2 tries to DELETE User 1's upload
        r_iso_del = client.delete(f"/api/uploads/{upload1_id}", headers=headers2)
        # User 2 lists uploads: User 1's upload should NOT be present
        r_iso_list = client.get("/api/uploads", headers=headers2)
        user2_uploads = [u.get("id") for u in r_iso_list.json()]

        iso_ok = (
            r_iso_get.status_code == 404 and
            r_iso_sum.status_code == 404 and
            r_iso_exp.status_code == 404 and
            r_iso_del.status_code == 404 and
            r_iso_list.status_code == 200 and
            (upload1_id not in user2_uploads)
        )
        record(
            "12. Account Isolation & Cross-User Security",
            iso_ok,
            f"GET: {r_iso_get.status_code}, Summary: {r_iso_sum.status_code}, Export: {r_iso_exp.status_code}, Delete: {r_iso_del.status_code}, upload1 not in user2 uploads: {upload1_id not in user2_uploads}"
        )
    except Exception as e:
        record("12. Account Isolation & Cross-User Security", False, str(e))

    # 13. Upload Deletion & Cleanup
    try:
        r_del = client.delete(f"/api/uploads/{upload1_id}", headers=headers1)
        r_get_after = client.get(f"/api/uploads/{upload1_id}", headers=headers1)
        del_ok = r_del.status_code == 204 and r_get_after.status_code == 404
        record(
            "13. Upload Deletion and Cleanup",
            del_ok,
            f"Delete status: {r_del.status_code}, Subsequent GET: {r_get_after.status_code}"
        )
    except Exception as e:
        record("13. Upload Deletion and Cleanup", False, str(e))

    # 14. Regression Test: Date Strings Normalization
    try:
        from app.file_parser import parse_date
        date_strings = [
            "2026-09-01 00:00:00",
            "2026-09-01T15:30:00",
            "2026-09-01",
            "01-09-2026",
            "09/01/2026",
            "01-Sep-2026",
            "2026/09/01",
        ]
        all_matched = all(parse_date(s) == "2026-09-01" for s in date_strings)
        invalid_handled = parse_date("not-a-valid-date") is None and parse_date("") is None
        record(
            "14. Regression: Date Strings Normalization",
            all_matched and invalid_handled,
            f"All {len(date_strings)} string formats parsed to '2026-09-01', invalid handled safely"
        )
    except Exception as e:
        record("14. Regression: Date Strings Normalization", False, str(e))

    # 15. Regression Test: Excel Dates & Auto-Mapping
    try:
        from app.file_parser import parse_date, normalise_and_validate
        from app.schemas import ColumnMapping
        from datetime import date

        excel_date_cases = [
            (pd.Timestamp("2026-09-01 00:00:00"), "2026-09-01"),
            (datetime(2026, 9, 1, 10, 30), "2026-09-01"),
            (date(2026, 9, 1), "2026-09-01"),
            (46266, "2026-09-01"),      # Excel serial integer
            (46266.0, "2026-09-01"),    # Excel serial float
            ("46266", "2026-09-01"),    # Excel serial as string
        ]
        excel_parsed_ok = all(parse_date(val) == expected for val, expected in excel_date_cases)

        # Test case-insensitive date column auto-detection and normalization
        sample_df = pd.DataFrame([
            {"Product Name": "Apple", "Qty": 5, "Price": 2.0, "Transaction Date": pd.Timestamp("2026-09-15 00:00:00")},
            {"Product Name": "Banana", "Qty": 10, "Price": 1.0, "Transaction Date": 46280}, # 2026-09-15
        ])
        mapping_auto = ColumnMapping(
            product_name="Product Name",
            quantity="Qty",
            unit_price="Price",
            transaction_date=None,  # unmapped, should auto-detect "Transaction Date"
        )
        accepted_records, _ = normalise_and_validate(sample_df, mapping_auto)
        auto_detect_ok = (
            len(accepted_records) == 2 and
            accepted_records[0]["transaction_date"] == "2026-09-15" and
            accepted_records[1]["transaction_date"] == "2026-09-15"
        )
        record(
            "15. Regression: Excel Dates & Auto-Mapping",
            excel_parsed_ok and auto_detect_ok,
            f"Excel cells/timestamps/serials matched: {excel_parsed_ok}, Case-insensitive auto-mapping: {auto_detect_ok}"
        )
    except Exception as e:
        record("15. Regression: Excel Dates & Auto-Mapping", False, str(e))

    print("=" * 60)
    passed_count = sum(1 for _, p, _ in test_results if p)
    total_count = len(test_results)
    print(f"RESULTS: {passed_count}/{total_count} CHECKS PASSED")
    print("=" * 60)
    return passed_count == total_count

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
