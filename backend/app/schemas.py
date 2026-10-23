"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime


# ── Uploads ───────────────────────────────────────────────────────────────────

class ColumnMapping(BaseModel):
    product_name: str
    quantity: str
    unit_price: Optional[str] = None
    transaction_date: Optional[str] = None
    transaction_time: Optional[str] = None
    date_format_pref: Optional[str] = "auto"  # "auto", "DMY", "MDY", "YMD"
    category: Optional[str] = None
    order_id: Optional[str] = None
    line_total: Optional[str] = None


class UploadPreviewResponse(BaseModel):
    columns: List[str]
    sample_rows: List[dict]
    row_count: int
    fingerprint: str
    temporal_analysis: Optional[Dict[str, Any]] = None


class ConfirmUploadRequest(BaseModel):
    filename: str
    fingerprint: str
    column_mapping: ColumnMapping


class UploadOut(BaseModel):
    id: str
    filename: str
    created_at: datetime
    status: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    validation_summary: Optional[dict] = None
    error_summary: Optional[str] = None


# ── Analytics ─────────────────────────────────────────────────────────────────

class SummaryOut(BaseModel):
    total_revenue: float
    total_units: int
    product_count: int
    order_count: int
    row_count: int
    best_product: Optional[str] = None
    best_month: Optional[str] = None


class ProductRow(BaseModel):
    rank: int
    product_name: str
    total_revenue: float
    total_quantity: int
    category: Optional[str] = None


class MonthlyRow(BaseModel):
    month: str
    revenue: float
    units_sold: int


class DayRow(BaseModel):
    day: int
    revenue: float
    units_sold: int


class AnalyticsStatusOut(BaseModel):
    upload_id: str
    status: str
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
