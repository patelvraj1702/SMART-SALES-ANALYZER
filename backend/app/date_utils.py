"""
Robust, reusable date and time normalization and auto-detection engine.
Handles:
- Common string formats: ISO, dash, slash, dot, named months
- Excel datetime objects, Python date/datetime/time, pandas Timestamps
- Excel serial dates (int/float) and serial times
- Time-only formats (24h, 12h AM/PM)
- Timezone-aware timestamps (preserving local calendar day)
- Ambiguity detection (e.g. 03/04/2026) with user-selectable preference (DMY, MDY, YMD, auto)
- Intelligent column detection inspecting both headers and sample row values
"""
import re
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Recognized header aliases
DATE_ALIASES = [
    "transaction_date",
    "transaction date",
    "sales_date",
    "sale_date",
    "order_date",
    "order date",
    "bill_date",
    "invoice_date",
    "created_at",
    "date",
    "txn_date",
    "txn date",
    "posting_date",
    "event_date",
]

TIME_ALIASES = [
    "transaction_time",
    "transaction time",
    "order_time",
    "order time",
    "sale_time",
    "sales_time",
    "time",
    "txn_time",
    "txn time",
    "bill_time",
]

COMBINED_ALIASES = [
    "transaction_datetime",
    "transaction datetime",
    "date_time",
    "datetime",
    "date time",
    "timestamp",
    "order_datetime",
    "sale_datetime",
]

# Standard datetime formats (ordered from most to least specific)
DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %I:%M %p",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%d %b %Y %H:%M:%S",
    "%d %b %Y %H:%M",
    "%d-%b-%Y %H:%M:%S",
    "%d-%b-%Y %H:%M",
]

DATE_ONLY_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d-%b-%Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %B %Y",
    "%Y%m%d",
]

TIME_ONLY_FORMATS = [
    "%H:%M:%S",
    "%H:%M",
    "%I:%M:%S %p",
    "%I:%M %p",
    "%I:%M:%S%p",
    "%I:%M%p",
]


def parse_time_value(val: Any) -> Optional[str]:
    """Parse time-only value to 'HH:mm:ss'."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, time):
        return val.strftime("%H:%M:%S")
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%H:%M:%S")

    # Excel time serial (0.0 to 1.0 fraction of day)
    if isinstance(val, float) and 0.0 <= val < 1.0:
        total_seconds = int(round(val * 86400))
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    s = str(val).strip()
    if not s or s.lower() in ("nan", "nat", "none", "null", ""):
        return None

    # Check direct formats
    for fmt in TIME_ONLY_FORMATS:
        try:
            return datetime.strptime(s, fmt).time().strftime("%H:%M:%S")
        except ValueError:
            continue

    # Regex search for 14:35(:20)? (AM|PM)?
    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?", s)
    if m:
        hr = int(m.group(1))
        mn = int(m.group(2))
        sc = int(m.group(3)) if m.group(3) else 0
        ampm = m.group(4)
        if ampm:
            ampm = ampm.upper()
            if ampm == "PM" and hr < 12:
                hr += 12
            elif ampm == "AM" and hr == 12:
                hr = 0
        if 0 <= hr <= 23 and 0 <= mn <= 59 and 0 <= sc <= 59:
            return f"{hr:02d}:{mn:02d}:{sc:02d}"

    return None


def parse_flexible_datetime(
    date_val: Any,
    time_val: Any = None,
    date_format_pref: str = "auto",
) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """
    Parse date, optional time, or combined datetime.
    Returns:
        (normalized_date, normalized_time, normalized_timestamp, is_ambiguous)
        - normalized_date: 'yyyy-MM-dd' or None
        - normalized_time: 'HH:mm:ss' or None
        - normalized_timestamp: 'yyyy-MM-ddTHH:mm:ss' or None
        - is_ambiguous: True if date format could be either DMY or MDY
    """
    pref = (date_format_pref or "auto").upper().strip()
    parsed_date: Optional[str] = None
    parsed_time: Optional[str] = None
    is_ambiguous: bool = False

    # 1. Native Python/Pandas types
    if isinstance(date_val, (datetime, pd.Timestamp)):
        parsed_date = date_val.strftime("%Y-%m-%d")
        if date_val.hour != 0 or date_val.minute != 0 or date_val.second != 0:
            parsed_time = date_val.strftime("%H:%M:%S")
    elif isinstance(date_val, date):
        parsed_date = date_val.strftime("%Y-%m-%d")
    elif isinstance(date_val, (int, float)) and not pd.isna(date_val):
        # Excel serial date (days since 1899-12-30)
        if 10000 <= date_val <= 100000:
            dt = pd.to_datetime(date_val, unit="D", origin="1899-12-30")
            parsed_date = dt.strftime("%Y-%m-%d")
            if isinstance(date_val, float) and (date_val % 1) > 0:
                parsed_time = dt.strftime("%H:%M:%S")

    # 2. String handling
    if parsed_date is None and date_val is not None and not pd.isna(date_val):
        s = str(date_val).strip()
        if s and s.lower() not in ("nan", "nat", "none", "null", ""):
            # Check numeric string serial (e.g. "46266" or "46266.5")
            try:
                num = float(s)
                if 10000 <= num <= 100000:
                    dt = pd.to_datetime(num, unit="D", origin="1899-12-30")
                    parsed_date = dt.strftime("%Y-%m-%d")
                    if (num % 1) > 0:
                        parsed_time = dt.strftime("%H:%M:%S")
            except ValueError:
                pass

        if parsed_date is None and s and s.lower() not in ("nan", "nat", "none", "null", ""):
            # Strip timezone offset only when attached to a time component to preserve the local calendar day
            # e.g. "2026-09-15T14:35:20+05:30" -> "2026-09-15T14:35:20" while leaving "15-09-2026" intact
            clean_s = re.sub(r"(\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s*(?:[+-]\d{2}:?\d{2}|Z)$", r"\1", s).strip()

            # Separate embedded time if present (e.g. "2026-09-15 14:35:20" or "15/09/2026 2:35 PM")
            time_part_match = re.search(r"\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)$", clean_s)
            embedded_time_str = None
            date_part_str = clean_s
            if time_part_match:
                embedded_time_str = time_part_match.group(1)
                date_part_str = clean_s[: time_part_match.start()].strip()

            # Check for ambiguity in numeric date e.g. "03/04/2026" or "03-04-2026"
            amb_match = re.match(r"^(\d{1,2})([/\-.])(\d{1,2})[/\-.](\d{4})$", date_part_str)
            if amb_match:
                n1 = int(amb_match.group(1))
                sep = amb_match.group(2)
                n2 = int(amb_match.group(3))
                yr = int(amb_match.group(4))
                if 1 <= n1 <= 12 and 1 <= n2 <= 12 and n1 != n2:
                    is_ambiguous = True
                    if pref == "MDY":
                        parsed_date = f"{yr:04d}-{n1:02d}-{n2:02d}"
                    elif pref == "DMY":
                        parsed_date = f"{yr:04d}-{n2:02d}-{n1:02d}"
                    else:  # auto: dash is commonly DD-MM-YYYY, slash is commonly MM/DD/YYYY
                        if sep == "-":
                            parsed_date = f"{yr:04d}-{n2:02d}-{n1:02d}"
                        else:
                            parsed_date = f"{yr:04d}-{n1:02d}-{n2:02d}"
                elif n1 > 12:
                    # Definitely Day first e.g. 15/09/2026
                    parsed_date = f"{yr:04d}-{n2:02d}-{n1:02d}"
                elif n2 > 12:
                    # Definitely Month first e.g. 09/15/2026
                    parsed_date = f"{yr:04d}-{n1:02d}-{n2:02d}"

            # Standard format parsing
            if parsed_date is None:
                all_formats = DATETIME_FORMATS + DATE_ONLY_FORMATS
                for fmt in all_formats:
                    try:
                        dt = datetime.strptime(clean_s, fmt)
                        parsed_date = dt.strftime("%Y-%m-%d")
                        if ("%H" in fmt or "%I" in fmt) and not parsed_time:
                            parsed_time = dt.strftime("%H:%M:%S")
                        break
                    except ValueError:
                        continue

            # Fallback using pandas.to_datetime
            if parsed_date is None:
                try:
                    dayfirst = (pref == "DMY")
                    dt = pd.to_datetime(clean_s, dayfirst=dayfirst, errors="coerce")
                    if pd.notna(dt):
                        parsed_date = dt.strftime("%Y-%m-%d")
                        if (dt.hour != 0 or dt.minute != 0 or dt.second != 0) and not parsed_time:
                            parsed_time = dt.strftime("%H:%M:%S")
                except Exception:
                    pass

            # Extract embedded time if we found one
            if embedded_time_str and not parsed_time:
                parsed_time = parse_time_value(embedded_time_str)

    # 3. Separate time column value
    if time_val is not None and not pd.isna(time_val):
        explicit_time = parse_time_value(time_val)
        if explicit_time:
            parsed_time = explicit_time

    # 4. If date_val was actually a time-only value (e.g. user selected time column as date)
    if parsed_date is None and parsed_time is None and date_val is not None and not pd.isna(date_val):
        standalone_time = parse_time_value(date_val)
        if standalone_time:
            parsed_time = standalone_time

    # 5. Build combined timestamp
    parsed_timestamp = None
    if parsed_date and parsed_time:
        parsed_timestamp = f"{parsed_date}T{parsed_time}"
    elif parsed_date:
        parsed_timestamp = f"{parsed_date}T00:00:00"

    return parsed_date, parsed_time, parsed_timestamp, is_ambiguous


def analyze_columns_temporal(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspect columns and cell values to detect candidate date and time columns,
    measure parse rates, and identify date/time ambiguity.
    """
    col_scores: Dict[str, Dict[str, Any]] = {}
    sample_size = min(len(df), 50)
    sample_df = df.head(sample_size)

    for col in df.columns:
        col_name = str(col).lower().strip()
        date_count = 0
        time_count = 0
        ambiguous_count = 0
        valid_examples = []

        # Name bonus
        has_date_name = any(a in col_name for a in ["date", "created_at", "timestamp"])
        has_time_name = any(a in col_name for a in ["time", "hour", "clock"]) and not has_date_name
        has_combined_name = any(a in col_name for a in ["datetime", "date_time", "timestamp"])

        for val in sample_df[col]:
            d, t, ts, amb = parse_flexible_datetime(val)
            if d:
                date_count += 1
            if t:
                time_count += 1
            if amb:
                ambiguous_count += 1
            if (d or t) and len(valid_examples) < 3:
                valid_examples.append({
                    "raw": str(val),
                    "normalized_date": d,
                    "normalized_time": t,
                    "normalized_timestamp": ts,
                    "is_ambiguous": amb,
                })

        col_scores[str(col)] = {
            "date_match_rate": date_count / max(1, sample_size),
            "time_match_rate": time_count / max(1, sample_size),
            "has_date_name": has_date_name or has_combined_name,
            "has_time_name": has_time_name,
            "has_combined_name": has_combined_name,
            "ambiguous_count": ambiguous_count,
            "examples": valid_examples,
        }

    # Identify candidate date and time columns
    candidate_date_cols = []
    candidate_time_cols = []

    for col, score in col_scores.items():
        if score["date_match_rate"] > 0.5 or (score["has_date_name"] and score["date_match_rate"] > 0.2):
            candidate_date_cols.append(col)
        if score["time_match_rate"] > 0.5 or (score["has_time_name"] and score["time_match_rate"] > 0.2):
            candidate_time_cols.append(col)

    # Best guesses
    best_date_col = None
    best_time_col = None

    if candidate_date_cols:
        best_date_col = max(
            candidate_date_cols,
            key=lambda c: (col_scores[c]["has_date_name"], col_scores[c]["date_match_rate"]),
        )

    # Time column should be different from date column unless column is combined datetime
    remaining_time_cols = [c for c in candidate_time_cols if c != best_date_col]
    if remaining_time_cols:
        best_time_col = max(
            remaining_time_cols,
            key=lambda c: (col_scores[c]["has_time_name"], col_scores[c]["time_match_rate"]),
        )

    # Determine overall temporal type
    temporal_type = "none"
    sample_evals = []
    total_ambiguous = 0
    valid_dates_count = 0
    valid_times_count = 0

    if best_date_col:
        for val in sample_df[best_date_col]:
            d, t, ts, amb = parse_flexible_datetime(val)
            if d:
                valid_dates_count += 1
            if t:
                valid_times_count += 1
            if amb:
                total_ambiguous += 1
            if len(sample_evals) < 4:
                sample_evals.append({
                    "raw": str(val),
                    "normalized_date": d,
                    "normalized_time": t,
                    "normalized_timestamp": ts,
                    "is_ambiguous": amb,
                })

        if valid_dates_count > 0 and (valid_times_count > 0 or best_time_col):
            temporal_type = "date_and_time"
        elif valid_dates_count > 0:
            temporal_type = "date_only"
    elif best_time_col:
        temporal_type = "time_only"
        for val in sample_df[best_time_col]:
            t = parse_time_value(val)
            if t:
                valid_times_count += 1
            if len(sample_evals) < 4:
                sample_evals.append({
                    "raw": str(val),
                    "normalized_date": None,
                    "normalized_time": t,
                    "normalized_timestamp": None,
                    "is_ambiguous": False,
                })

    return {
        "detected_date_col": best_date_col,
        "detected_time_col": best_time_col,
        "temporal_type": temporal_type,
        "sample_evaluations": sample_evals,
        "valid_dates_count": valid_dates_count,
        "valid_times_count": valid_times_count,
        "missing_count": sample_size - max(valid_dates_count, valid_times_count),
        "invalid_count": 0,
        "ambiguous_count": total_ambiguous,
        "detected_ambiguity": total_ambiguous > 0,
        "candidate_date_columns": candidate_date_cols,
        "candidate_time_columns": candidate_time_cols,
    }
