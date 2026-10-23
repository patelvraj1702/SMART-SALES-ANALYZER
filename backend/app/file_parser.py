"""
File parsing, column validation, and normalisation utilities.

Canonical fields:
  product_name, quantity, unit_price, revenue (computed),
  transaction_date, transaction_time, transaction_datetime, category, order_id
"""
import hashlib
import io
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.schemas import ColumnMapping
from app.date_utils import (
    parse_flexible_datetime,
    analyze_columns_temporal,
    DATE_ALIASES,
    TIME_ALIASES,
    COMBINED_ALIASES,
)


def compute_fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def read_file(content: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or XLSX into a DataFrame with multi-sheet detection."""
    name_lower = filename.lower()
    if name_lower.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
    elif name_lower.endswith((".xlsx", ".xls")):
        excel_file = pd.ExcelFile(io.BytesIO(content))
        # Select best sheet: look for sales/data/transactions sheet, else sheet 0
        target_sheet = excel_file.sheet_names[0]
        for name in excel_file.sheet_names:
            clean = name.lower().strip()
            if any(k in clean for k in ["sales", "data", "transaction", "order", "records"]):
                target_sheet = name
                break
        return pd.read_excel(excel_file, sheet_name=target_sheet)
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def parse_date(value: Any) -> Optional[str]:
    """Backward-compatible helper returning normalized 'yyyy-MM-dd' or None."""
    d, _, _, _ = parse_flexible_datetime(value)
    return d


def parse_numeric(value: Any) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    try:
        clean = re.sub(r"[^\d.\-]", "", str(value))
        return float(clean)
    except (ValueError, TypeError):
        return None


def _resolve_column(df: pd.DataFrame, mapped_col: Optional[str], alias_list: List[str]) -> Optional[str]:
    """Find matching column name directly, case-insensitively, or via aliases."""
    if mapped_col:
        # 1. Exact match
        if mapped_col in df.columns:
            return mapped_col
        # 2. Case-insensitive / whitespace-normalized match
        target = str(mapped_col).strip().lower()
        for c in df.columns:
            if str(c).strip().lower() == target:
                return c
            if re.sub(r"[\s_-]+", " ", str(c).lower().strip()) == re.sub(r"[\s_-]+", " ", target):
                return c

    # 3. Auto-detect from aliases
    cols_clean = {re.sub(r"[\s_-]+", " ", str(c).lower().strip()): c for c in df.columns}
    for alias in alias_list:
        norm_alias = re.sub(r"[\s_-]+", " ", alias.lower().strip())
        if norm_alias in cols_clean:
            return cols_clean[norm_alias]

    return None


def normalise_and_validate(
    df: pd.DataFrame,
    mapping: ColumnMapping,
) -> Tuple[List[dict], List[dict]]:
    """
    Apply column mapping, compute revenue, validate rows, and normalize date/time.

    Returns (accepted_records, rejected_records).
    Each accepted record is a dict ready for MongoDB insertion and Spark input.
    Each rejected record has 'row_index' and 'errors' keys.
    """
    accepted: List[dict] = []
    rejected: List[dict] = []

    use_line_total = bool(mapping.line_total)

    # ── Resolve date and time column names ────────────────────────────────────
    date_col = _resolve_column(df, mapping.transaction_date, DATE_ALIASES + COMBINED_ALIASES)
    time_col = _resolve_column(df, mapping.transaction_time, TIME_ALIASES)

    # If time column ended up identical to date column, keep as combined
    if date_col and time_col and date_col == time_col:
        time_col = None

    # Date format interpretation preference ("auto", "DMY", "MDY", "YMD")
    pref = getattr(mapping, "date_format_pref", "auto") or "auto"

    for idx, row in df.iterrows():
        errors: List[str] = []

        # ── Required: product_name ────────────────────────────────────────────
        product_name = str(row.get(mapping.product_name, "")).strip()
        if not product_name:
            errors.append("Missing product_name")

        # ── Required: quantity ────────────────────────────────────────────────
        qty_raw = row.get(mapping.quantity, "")
        quantity = parse_numeric(qty_raw)
        if quantity is None:
            errors.append(f"Invalid quantity: '{qty_raw}'")
        elif quantity <= 0:
            errors.append(f"Quantity must be positive, got {quantity}")

        # ── Revenue calculation ───────────────────────────────────────────────
        revenue: Optional[float] = None
        unit_price: Optional[float] = None

        if use_line_total and mapping.line_total:
            lt_raw = row.get(mapping.line_total, "")
            line_total = parse_numeric(lt_raw)
            if line_total is None:
                errors.append(f"Invalid line_total: '{lt_raw}'")
            elif line_total < 0:
                errors.append(f"line_total must be non-negative, got {line_total}")
            else:
                revenue = line_total
        else:
            up_raw = row.get(mapping.unit_price or "", "")
            unit_price = parse_numeric(up_raw)
            if unit_price is None:
                errors.append(f"Invalid unit_price: '{up_raw}'")
            elif unit_price < 0:
                errors.append(f"unit_price must be non-negative, got {unit_price}")
            elif quantity and quantity > 0 and unit_price >= 0:
                revenue = round(quantity * unit_price, 4)

        if revenue is None and not errors:
            errors.append("Cannot compute revenue")

        # ── Date & Time parsing ───────────────────────────────────────────────
        date_raw = row.get(date_col) if date_col else None
        time_raw = row.get(time_col) if time_col else None

        tx_date, tx_time, tx_datetime, _ = parse_flexible_datetime(
            date_raw, time_raw, date_format_pref=pref
        )

        # ── Optional fields ───────────────────────────────────────────────────
        category: Optional[str] = None
        if mapping.category:
            cat_val = str(row.get(mapping.category, "")).strip()
            category = cat_val if cat_val and cat_val.lower() != "nan" else None

        order_id: Optional[str] = None
        if mapping.order_id:
            oid_val = str(row.get(mapping.order_id, "")).strip()
            order_id = oid_val if oid_val and oid_val.lower() != "nan" else None

        # ── Accept or reject ──────────────────────────────────────────────────
        if errors:
            rejected.append({"row_index": int(idx) + 2, "errors": errors})
        else:
            accepted.append({
                "product_name": product_name,
                "quantity": float(quantity),  # type: ignore
                "unit_price": unit_price,
                "revenue": float(revenue),  # type: ignore
                "transaction_date": tx_date,
                "transaction_time": tx_time,
                "transaction_datetime": tx_datetime,
                "category": category,
                "order_id": order_id,
            })

    return accepted, rejected
