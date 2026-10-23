"""Spark job runner: writes CSV, runs spark-submit, parses JSON output."""
import csv
import json
import logging
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Normalised CSV columns the Scala app expects
SPARK_COLUMNS = [
    "product_name", "quantity", "unit_price", "revenue",
    "transaction_date", "transaction_time", "transaction_datetime",
    "category", "order_id",
]


import shutil

def _get_spark_jar() -> Optional[Path]:
    """Return absolute path to the assembly JAR, or None if not built yet."""
    # 1. Relative to project root based on this file's location
    project_root = Path(__file__).resolve().parent.parent.parent
    jar = project_root / settings.SPARK_JAR
    if jar.exists():
        return jar
    # 2. Relative to current working directory
    cwd = Path.cwd()
    if (cwd / settings.SPARK_JAR).exists():
        return cwd / settings.SPARK_JAR
    if (cwd.parent / settings.SPARK_JAR).exists():
        return cwd.parent / settings.SPARK_JAR
    # 3. Direct path
    jar_direct = Path(settings.SPARK_JAR)
    if jar_direct.exists():
        return jar_direct
    return None


def _get_spark_submit() -> str:
    """Return path or binary name for spark-submit."""
    configured = Path(settings.SPARK_SUBMIT)
    if configured.exists():
        return str(configured)
    which_cmd = shutil.which("spark-submit") or shutil.which("spark-submit.cmd")
    if which_cmd:
        return which_cmd
    return settings.SPARK_SUBMIT


def run_spark_job(records: List[dict], job_id: str) -> Dict[str, Any]:
    """
    Write records to a temp CSV, execute spark-submit, parse result JSON.
    Returns the analytics dict from the Scala engine.
    """
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)

    input_csv = temp_dir / f"{job_id}_input.csv"
    output_json = temp_dir / f"{job_id}_output.json"

    try:
        # ── 1. Write normalised CSV ───────────────────────────────────────────
        with open(input_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SPARK_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for rec in records:
                writer.writerow({
                    "product_name": rec.get("product_name", ""),
                    "quantity": rec.get("quantity", ""),
                    "unit_price": rec.get("unit_price", "") if rec.get("unit_price") is not None else "",
                    "revenue": rec.get("revenue", ""),
                    "transaction_date": rec.get("transaction_date", "") or "",
                    "transaction_time": rec.get("transaction_time", "") or "",
                    "transaction_datetime": rec.get("transaction_datetime", "") or "",
                    "category": rec.get("category", "") or "",
                    "order_id": rec.get("order_id", "") or "",
                })

        # ── 2. Locate JAR ────────────────────────────────────────────────────
        jar_path = _get_spark_jar()
        if not jar_path:
            raise FileNotFoundError(
                f"Spark JAR not found at '{settings.SPARK_JAR}'. "
                "Run 'sbt assembly' inside the spark-engine directory."
            )

        # ── 3. Build spark-submit command ─────────────────────────────────────
        # Use absolute paths; avoid shell injection by using a list
        cmd = [
            _get_spark_submit(),
            "--master", "local[*]",
            "--class", "com.smartsales.SalesAnalyzer",
            "--conf", "spark.ui.enabled=false",
            "--conf", "spark.driver.memory=1g",
            str(jar_path),
            str(input_csv.resolve()),
            str(output_json.resolve()),
            job_id,
        ]

        logger.info("Running Spark job %s", job_id)
        logger.debug("Command: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.SPARK_TIMEOUT_SECONDS,
        )

        if result.returncode != 0:
            stderr_tail = result.stderr[-2000:] if result.stderr else ""
            raise RuntimeError(f"spark-submit failed (rc={result.returncode}):\n{stderr_tail}")

        # ── 4. Parse output JSON ───────────────────────────────────────────────
        if not output_json.exists():
            raise FileNotFoundError("Spark job produced no output file")

        with open(output_json, "r", encoding="utf-8") as f:
            analytics = json.load(f)

        return analytics

    finally:
        # ── 5. Cleanup temp files ──────────────────────────────────────────────
        for path in [input_csv, output_json]:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass
