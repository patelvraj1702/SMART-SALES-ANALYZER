# Smart Sales Analyzer — System Architecture & Data Flow

This document details the architecture, component interaction, and security model of the **Smart Sales Analyzer** application.

```
       +-------------------------------------------------------------+
       |                        Web Browser                          |
       |  React 19 + Vite + Tailwind CSS + Recharts + React Router   |
       +------------------------------+------------------------------+
                                      |
                      HTTP / REST API | (JWT Bearer Token)
                                      v
       +-------------------------------------------------------------+
       |                    FastAPI Backend (Python)                 |
       |  - Authentication (JWT + Bcrypt)                            |
       |  - Strict Multi-Tenant Account Isolation                    |
       |  - File Ingestion & Parsing (Pandas / OpenpyXL)             |
       |  - Column Mapping & Schema Normalisation                    |
       |  - Spark Job Coordinator (Process Subprocess Orchestration) |
       +---------------+-----------------------------+---------------+
                       |                             |
      MongoDB PyMongo  |                             | spark-submit CLI
      & Motor Async    |                             | (Local Process)
                       v                             v
       +-------------------------------+   +-------------------------------------+
       |         MongoDB 7.0+          |   |     Apache Spark 3.5.x (Scala 2.12) |
       |  Collections:                 |   |  - DataFrame & Spark SQL Engine     |
       |   - users                     |   |  - Product Rankings (Revenue & Qty) |
       |   - uploads                   |   |  - Monthly Sales Aggregation        |
       |   - sales_records             |   |  - Day-of-Month (1-31) Distribution |
       |   - analytics_results         |   |  - JSON Metric Export               |
       |  Compound Indexes on:         |   +-------------------------------------+
       |   (owner_id, upload_id)       |
       +-------------------------------+
```

---

## Component Roles

### 1. Frontend (`frontend/`)
- **Technology**: React 19, Vite, Tailwind CSS, Recharts, Lucide Icons, React Router v7.
- **Role**: Single-Page Application (SPA) providing store owners with an interactive, responsive analytics experience.
- **Pages**:
  - `Login` & `SignUp`: Authentication with form validation and feedback.
  - `Dashboard`: KPI summary cards (Total Revenue, Units Sold, Product Count, Order Count, Best-Selling Product, Best Month), Monthly Sales Line Chart, Product Revenue Ranking Chart, Day-of-Month Sales Distribution.
  - `UploadSales`: Drag-and-drop CSV/XLSX file upload, preview, interactive column mapping, row validation summary, and processing indicator.
  - `ProductAnalytics`: Sortable rankings by revenue or quantity, category display, and performance table.
  - `TimeAnalytics`: Dual-axis monthly revenue and volume chart, day-of-month breakdown (days 1-31), peak analysis.
  - `UploadHistory`: List of uploaded datasets, row counts, status badges, dataset switching, and dataset deletion with confirmation.
  - `Reports`: Authenticated CSV downloads for Product Rankings, Monthly Analytics, and Day-of-Month Analytics.

### 2. Backend (`backend/`)
- **Technology**: Python 3.10+, FastAPI, Pydantic v2, Motor (async MongoDB driver), PyJWT / python-jose, Passlib / bcrypt.
- **Role**: API Gateway, business logic, session/token management, data normalisation, and Spark execution management.
- **Security & Data Isolation**:
  - All protected endpoints derive the caller's `user_id` from the verified JWT bearer token.
  - Every MongoDB query, read, write, update, delete, and analytics lookup enforces `{"owner_id": user_id, ...}`.
  - Cross-user data leaks are prevented at the database query level.

### 3. Big Data Processing Engine (`spark-engine/`)
- **Technology**: Apache Spark 3.5.3, Scala 2.12.18, SBT (Simple Build Tool), sbt-assembly.
- **Role**: High-performance local distributed DataFrame and Spark SQL aggregation engine.
- **Operations**:
  - Ingests normalised CSV data.
  - Casts types and handles missing/malformed values gracefully.
  - Computes product metrics: Revenue sum, Quantity sum, rankings.
  - Computes time series: Calendar month (`yyyy-MM`) aggregations, day-of-month (1 to 31) aggregations.
  - Exports a clean, structured JSON payload consumed by FastAPI.

### 4. Database Layer (`MongoDB`)
- Stores user credentials (securely hashed with bcrypt).
- Stores upload metadata, validation summaries, and status.
- Stores individual row-level sales records with compound indexes on `(owner_id, upload_id)`.
- Stores computed Spark analytics results for sub-second dashboard rendering.
