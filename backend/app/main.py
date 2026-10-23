"""
Smart Sales Analyzer — FastAPI Backend
Entrypoint: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routers import auth, uploads, analytics, exports


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Smart Sales Analyzer API",
    version="1.0.0",
    description="Analytics platform for store sales data powered by Apache Spark",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",     tags=["Authentication"])
app.include_router(uploads.router,   prefix="/api/uploads",  tags=["Uploads"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(exports.router,   prefix="/api/exports",  tags=["Exports"])


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "Smart Sales Analyzer"}
