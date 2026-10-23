# Smart Sales Analyzer

[![Build & Test](https://img.shields.io/badge/Essential%20Tests-13%2F13%20Passed-brightgreen)](backend/test_essential.py)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-blue)](frontend)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal)](backend)
[![Apache Spark](https://img.shields.io/badge/Big%20Data-Apache%20Spark%203.5-orange)](spark-engine)
[![Scala](https://img.shields.io/badge/Engine-Scala%202.12-red)](spark-engine)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%207.0%2B-green)](backend)

**Smart Sales Analyzer** is a full-stack Big Data sales analytics web application built for store owners. It provides secure account management, CSV and Excel (`.xlsx`) sales data ingestion, column mapping, and interactive dashboards powered by a real **Apache Spark (Scala)** aggregation engine running locally via `spark-submit`.

---

## 1. Project Objectives & Core Questions Answered

Store owners can upload raw transaction logs from spreadsheets or point-of-sale systems to instantly answer:
- **Which products sell the most?** Product ranking by total unit sales.
- **Which products generate the highest revenue?** Product ranking and Pareto breakdown by total revenue.
- **Which month has the highest sales?** Monthly calendar aggregation (`yyyy-MM`) with revenue and volume trends.
- **Which days of the month have the highest sales?** Day-of-month breakdown (days 1–31) to identify peak payroll or shopping periods.
- **How many units have been sold and what is total revenue?** Real-time summary cards with order counts and distinct product tallies.
- **How does performance evolve over time?** Interactive dual-axis trend charts with tooltips and responsive filters.

This application is designed as a single-store-per-account college/capstone project with strict **data isolation** enforced across all database queries.

---

## 2. System Architecture & Data Flow

```
                      +------------------------------------+
                      |     Web Browser (Store Owner)      |
                      |  React 19 + Tailwind CSS + Recharts|
                      +-----------------+------------------+
                                        |
                         REST API (JWT) | HTTPS / JSON
                                        v
                      +-----------------+------------------+
                      |         FastAPI Backend            |
                      |  - JWT Authentication & Bcrypt     |
                      |  - File Ingestion & Normalisation  |
                      |  - Per-User Ownership Enforcement  |
                      |  - Spark Job Coordinator           |
                      +--------+------------------+--------+
                               |                  |
           PyMongo / Motor     |                  | Local Process Subprocess
           Async Driver        |                  | (spark-submit.cmd)
                               v                  v
                 +-------------+----+     +-------+--------------------+
                 |   MongoDB 7.0+   |     | Apache Spark 3.5.x (Scala) |
                 | - Users          |     | - Ingests normalised CSV   |
                 | - Uploads        |     | - Computes GroupBys & SQL  |
                 | - Sales Records  |     | - Generates JSON Analytics |
                 | - Analytics      |     +----------------------------+
                 +------------------+
```

See [docs/architecture.md](docs/architecture.md) for full architectural documentation.

---

## 3. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS, Recharts, Lucide Icons, React Router v7 |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, Motor (Async MongoDB), PyJWT, Bcrypt, Pandas, OpenpyXL |
| **Database** | MongoDB 7.0+ with compound indexes on `(owner_id, upload_id)` |
| **Big Data Engine** | Apache Spark 3.5.x, Scala 2.12.18, SBT, sbt-assembly |
| **Supported Files** | CSV (`.csv`), Excel (`.xlsx`, `.xls`) |

> [!NOTE]
> Sales aggregation is **genuinely executed via Scala and Apache Spark DataFrames**. It is not replaced with Pandas-only calculations or mocked static results.

---

## 4. Project Structure

```
SMART SALES ANALYZER/
├── backend/                  # FastAPI REST API & Spark Coordinator
│   ├── app/
│   │   ├── auth.py           # Bcrypt password hashing & JWT token validation
│   │   ├── config.py         # Environment configuration (Pydantic Settings)
│   │   ├── database.py       # Motor async MongoDB connection & index setup
│   │   ├── file_parser.py    # CSV/Excel parsing, row validation & mapping
│   │   ├── main.py           # FastAPI entrypoint & middleware configuration
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── spark_runner.py   # Spawns spark-submit & collects JSON results
│   │   └── routers/
│   │       ├── auth.py       # Signup, login, logout, me endpoints
│   │       ├── uploads.py    # Preview, validate, confirm, list, delete
│   │       ├── analytics.py  # Summary, products, monthly, day-of-month
│   │       └── exports.py    # Authenticated CSV reports
│   ├── test_essential.py     # 13-point end-to-end automated test suite
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Backend configuration
├── frontend/                 # React 19 Vite Single Page Application
│   ├── src/
│   │   ├── api.js            # Axios client with JWT interceptor
│   │   ├── components/ui.jsx # Metric cards, tables, banners, loading states
│   │   ├── context/
│   │   │   ├── AuthContext.jsx    # Session & JWT lifecycle
│   │   │   └── DatasetContext.jsx # Selected upload state management
│   │   ├── layouts/
│   │   │   └── DashboardLayout.jsx # Collapsible sidebar & header
│   │   └── pages/
│   │       ├── Login.jsx           # Store owner login
│   │       ├── SignUp.jsx          # New account registration
│   │       ├── Dashboard.jsx       # Real-time overview KPI dashboard
│   │       ├── UploadSales.jsx     # Drag-and-drop file upload & mapping
│   │       ├── ProductAnalytics.jsx # Product revenue & volume tables/charts
│   │       ├── TimeAnalytics.jsx   # Monthly & day-of-month time series
│   │       ├── UploadHistory.jsx   # Dataset switching & safe deletion
│   │       └── Reports.jsx         # Authenticated CSV export page
│   ├── package.json
│   └── vite.config.js
├── spark-engine/             # Standalone Scala Spark Analytics Engine
│   ├── src/main/scala/com/smartsales/
│   │   └── SalesAnalyzer.scala # Spark DataFrame aggregation code
│   ├── project/plugins.sbt   # sbt-assembly plugin
│   ├── build.sbt             # Spark & Jackson dependencies
│   └── target/scala-2.12/
│       └── smart-sales-analyzer-spark-assembly-1.0.0.jar
├── sample-data/
│   └── sales_sample.csv      # Sample retail sales dataset (44 rows, 7 products)
├── docs/
│   └── architecture.md       # Technical architecture specification
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

---

## 5. Prerequisites & Environment Setup

Verify the following tools are installed:

- **Java JDK**: Version 11 or 17 (Eclipse Temurin or OpenJDK recommended)
- **Scala**: Version 2.12.x (installed via sbt)
- **Apache Spark**: Version 3.5.x (installed in `C:\spark` or in system `PATH`)
- **Python**: Version 3.10+ (tested on Python 3.14)
- **Node.js**: Version 18+ (tested on Node.js 24)
- **MongoDB**: Version 6.0+ or 7.0+ (running locally on port `27017`)

---

### Quick Start (One-Click Windows Launcher)

Simply double-click:
```
run_app.bat
```
*(or run `start_app.bat`)*

This script automatically:
1. Checks that the local **MongoDB** service is running (and starts it if necessary).
2. Detects your **Python** installation (`py -3.14`, `py`, or `python`).
3. Verifies **Node.js** and **npm**.
4. Starts the **FastAPI backend** (Port `8000`) and **React/Vite frontend** (Port `5173`) in dedicated console windows.
5. Launches your default web browser directly to **`http://localhost:5173`**.

To stop all running servers at any time, run **`stop_app.bat`** or press `S` in the launcher window.

---

### Manual Setup & Execution

### Step 1: Clone & Configure Environment

Copy `.env.example` to `backend/.env`:
```bash
cp .env.example backend/.env
```
Ensure your `backend/.env` has valid local parameters:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=smart_sales_analyzer
JWT_SECRET=super_secret_jwt_key_at_least_32_characters_long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
SPARK_HOME=C:\spark
SPARK_SUBMIT=C:\spark\bin\spark-submit.cmd
SPARK_JAR=spark-engine\target\scala-2.12\smart-sales-analyzer-spark-assembly-1.0.0.jar
```

### Step 2: Build the Scala Spark Assembly JAR

From the `spark-engine/` directory:
```bash
cd spark-engine
sbt assembly
cd ..
```
*This compiles `SalesAnalyzer.scala` and packages `smart-sales-analyzer-spark-assembly-1.0.0.jar` with Jackson dependencies.*

### Step 3: Install Backend Dependencies & Start API

From the `backend/` directory:
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API docs will be live at `http://127.0.0.1:8000/docs`.*

### Step 4: Install Frontend Dependencies & Start App

In a separate terminal, from the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```
*The web application will open at `http://localhost:5173`.*

---

## 7. Sample Data & Column Mapping

The system ships with a ready-to-use sample dataset located in:
`sample-data/sales_sample.csv`

Columns in sample:
```csv
order_id,product_name,category,quantity,unit_price,transaction_date
ORD-001,Wireless Headphones,Electronics,3,49.99,2024-01-05
ORD-002,USB-C Cable,Electronics,10,9.99,2024-01-07
ORD-003,Desk Lamp,Home Office,2,34.99,2024-01-10
...
```

### Supported Columns & Mapping Rules

When importing files with custom or messy column headers, the upload wizard allows mapping to standard fields:

| Canonical Field | Required? | Description |
|---|---|---|
| `product_name` | **Required** | Name or SKU of the product sold |
| `quantity` | **Required** | Positive integer or float (e.g. `Qty`, `Units`) |
| `unit_price` | **Required\*** | Price per unit (e.g. `Price`, `Rate`). \*Required if no line total |
| `line_total` | *Optional* | Pre-computed total (e.g. `Total`, `Amount`) |
| `transaction_date`| *Optional* | Sale date (formats: `YYYY-MM-DD`, `DD-MM-YYYY`, `MM/DD/YYYY`) |
| `category` | *Optional* | Product category (e.g. `Electronics`, `Kitchen`) |
| `order_id` | *Optional* | Unique transaction or invoice identifier |

### Revenue Calculation Rules
1. If a valid `line_total` column is selected, revenue is taken directly from that field.
2. Otherwise, revenue is calculated as `quantity * unit_price`.
3. Negative quantities and negative prices are flagged and rejected in the preview.

---

## 8. Backend API Reference

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | Service health status | No |
| `POST` | `/api/auth/signup` | Register new store owner | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT token | No |
| `POST` | `/api/auth/logout` | Invalidate client session | Yes |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | Yes |
| `POST` | `/api/uploads/preview` | Upload and preview sample rows & columns | Yes |
| `POST` | `/api/uploads` | Confirm import, store rows & run Spark | Yes |
| `GET` | `/api/uploads` | List user's upload history | Yes |
| `GET` | `/api/uploads/{id}` | Get upload details & validation summary | Yes |
| `DELETE`| `/api/uploads/{id}` | Delete upload, records, and analytics | Yes |
| `GET` | `/api/analytics/{id}/summary` | KPI cards, best product & best month | Yes |
| `GET` | `/api/analytics/{id}/products`| Ranked product list by revenue & units | Yes |
| `GET` | `/api/analytics/{id}/monthly` | Monthly aggregated sales & units | Yes |
| `GET` | `/api/analytics/{id}/day-of-month` | Day 1–31 sales distribution | Yes |
| `POST` | `/api/analytics/{id}/process`| Manually re-trigger Spark execution | Yes |
| `GET` | `/api/exports/{id}/products.csv` | Download product rankings as CSV | Yes |
| `GET` | `/api/exports/{id}/monthly.csv` | Download monthly sales as CSV | Yes |
| `GET` | `/api/exports/{id}/day-of-month.csv` | Download daily sales distribution | Yes |

---

## 9. Essential Automated Tests & Verification

The project includes an end-to-end integration test suite located at `backend/test_essential.py`.

To run the verification suite:
```bash
cd backend
python test_essential.py
```

### Verified Test Results (Executed on 22-Oct-2026)

```
============================================================
STARTING ESSENTIAL TEST SUITE: SMART SALES ANALYZER
============================================================
[PASS] 1. Backend Health Check: Status: 200, Body: {'status': 'ok', 'service': 'Smart Sales Analyzer'}
[PASS] 2. User 1 Registration: Status 201, Token generated: True
[PASS] 3. User 1 Login: Status 200
[PASS] 4. User 2 Registration (Isolation Target): Status 201
[PASS] 5. Rejection of Unauthenticated Requests: Status 401
[PASS] 6. CSV Upload & Spark Processing: Upload ID: 6ada10ed18eef37406dfd7ae, Status: ready, Accepted rows: 44
[PASS] 7. Summary Metrics & Revenue Accuracy: Revenue: 6106.49, Units: 351, Best Product: Mechanical Keyboard
[PASS] 8. Product Analytics & Ranking: Count: 7, Top: Mechanical Keyboard ($1259.86)
[PASS] 9. Time Analytics (Monthly & Day-of-Month): Months count: 6, Days count: 20
[PASS] 10. CSV Exports Download: Products CSV length: 330 bytes, Monthly CSV length: 142 bytes
[PASS] 11. Excel (.xlsx) Upload & Spark Processing: Status: 201, Status field: ready
[PASS] 12. Account Isolation & Cross-User Security: GET: 404, Summary: 404, Export: 404, Delete: 404, upload1 not in user2 uploads: True
[PASS] 13. Upload Deletion and Cleanup: Delete status: 204, Subsequent GET: 404
============================================================
RESULTS: 13/13 CHECKS PASSED
============================================================
```

---

## 10. Troubleshooting Common Issues

### 1. `Spark JAR not found at spark-engine\target\...`
- **Solution**: Run `sbt assembly` inside the `spark-engine` directory before launching the backend. Verify that the JAR is created in `spark-engine/target/scala-2.12/smart-sales-analyzer-spark-assembly-1.0.0.jar`.

### 2. `spark-submit: command not found` or Java Exception
- **Solution**: Verify that `SPARK_HOME` points to your Spark directory (e.g. `C:\spark`) and Java 11 or 17 is on your `PATH`.
- In Windows, ensure `JAVA_HOME` does not contain spaces.

### 3. `ServerSelectionTimeoutError` / MongoDB Connection Refused
- **Solution**: Check that the MongoDB service is running:
  - Windows: `Get-Service MongoDB` (PowerShell) or `net start MongoDB`
  - Linux/Mac: `sudo systemctl status mongod` or `brew services start mongodb-community`

### 4. CORS Errors in Frontend
- **Solution**: Ensure your frontend is running on `http://localhost:5173` or `http://127.0.0.1:5173`, which are listed in `backend/app/config.py` under `CORS_ORIGINS`.

---

## 11. Known Limitations

- **Hourly Analytics**: Hourly time grouping is deliberately omitted in this version as transaction timestamp granularity varies across college/retail POS spreadsheets.
- **Single Store per Account**: Each registered user manages datasets for their own store. Multi-store branch consolidation across different tenant accounts is not included.
- **Synchronous Spark Processing**: Designed for local development and demonstration with datasets up to 500,000 rows. Distributed cluster submission (YARN/Kubernetes) is not required for local college evaluation.
