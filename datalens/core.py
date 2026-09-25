"""Schema-flexible analytics pipeline used by the CLI and Streamlit app."""

from __future__ import annotations

import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ALIASES = {
    "id": ["transaction_id", "order_id", "event_id", "id"],
    "customer": ["customer_id", "user_id", "account_id"],
    "date": ["transaction_date", "order_date", "purchase_date", "date", "timestamp"],
    "amount": ["amount", "purchase_amount", "order_amount", "revenue", "total_spent", "lifetime_value"],
    "segment": ["customer_segment", "customer_type", "segment", "tier", "category"],
    "product": ["product", "product_name", "product_category", "category"],
    "status": ["payment_status", "order_status", "status"],
    "location": ["location", "city", "region", "country"],
}


def load_dataset(source: str | Path | bytes | io.BytesIO, filename: str | None = None) -> pd.DataFrame:
    """Load CSV or JSON without mutating the source."""
    name = filename or str(source)
    suffix = Path(name).suffix.lower()
    if isinstance(source, (bytes, bytearray)):
        stream = io.BytesIO(source)
    else:
        stream = source
    if suffix == ".json":
        payload = json.load(stream) if hasattr(stream, "read") else json.loads(Path(source).read_text(encoding="utf-8"))
        return pd.json_normalize(payload)
    if suffix not in {".csv", ""}:
        raise ValueError("DataLens supports CSV and JSON files only.")
    return pd.read_csv(stream, encoding="utf-8")


def detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    lower = {str(column).lower(): column for column in df.columns}
    detected: dict[str, str | None] = {}
    for role, names in ALIASES.items():
        detected[role] = next((lower[name] for name in names if name in lower), None)
    if detected["date"] is None:
        for column in df.columns:
            parsed = pd.to_datetime(df[column], format="mixed", errors="coerce")
            if parsed.notna().mean() >= 0.8 and not pd.api.types.is_numeric_dtype(df[column]):
                detected["date"] = column
                break
    if detected["amount"] is None:
        numeric = df.select_dtypes(include="number").columns
        amount_tokens = ("amount", "revenue", "sales", "value", "spend", "price", "cost", "total")
        detected["amount"] = next(
            (column for column in numeric if any(token in str(column).lower() for token in amount_tokens)),
            None,
        )
    return detected


def profile_dataset(df: pd.DataFrame) -> dict[str, Any]:
    rows = len(df)
    columns = []
    for name in df.columns:
        series = df[name]
        item: dict[str, Any] = {
            "column": str(name),
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 2) if rows else 0,
            "unique": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            for key, method in [("min", "min"), ("max", "max"), ("mean", "mean"), ("median", "median"), ("std", "std")]:
                value = getattr(series, method)()
                item[key] = round(float(value), 4) if pd.notna(value) else None
        elif pd.api.types.is_object_dtype(series):
            item["top_values"] = {str(key): int(value) for key, value in series.value_counts(dropna=True).head(5).items()}
        columns.append(item)
    return {
        "rows": rows,
        "columns": len(df.columns),
        "memory_mb": round(float(df.memory_usage(deep=True).sum() / 1_000_000), 3),
        "duplicates": int(df.duplicated().sum()),
        "numeric_columns": int(len(df.select_dtypes(include="number").columns)),
        "categorical_columns": int(len(df.select_dtypes(include=["str", "category"]).columns)),
        "date_columns": int(sum(_date_like(df[column]) for column in df.columns)),
        "column_profile": columns,
    }


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    cleaned = df.copy()
    before = len(cleaned)
    cleaned.columns = [str(column).strip().lower().replace(" ", "_") for column in cleaned.columns]
    cleaned = cleaned.drop_duplicates().copy()
    for column in cleaned.select_dtypes(include="str").columns:
        cleaned[column] = cleaned[column].astype("string").str.strip().replace({"": pd.NA})
    numeric_columns = list(cleaned.select_dtypes(include="number").columns)
    for column in numeric_columns:
        if cleaned[column].isna().any():
            cleaned[column] = cleaned[column].fillna(cleaned[column].median())
    for column in cleaned.columns:
        if any(token in column for token in ("date", "time", "timestamp")):
            parsed = pd.to_datetime(cleaned[column], format="mixed", errors="coerce")
            if parsed.notna().mean() >= 0.5:
                cleaned[column] = parsed
    return cleaned, {"rows_before": before, "rows_after": len(cleaned), "duplicates_removed": before - len(cleaned), "numeric_imputed": numeric_columns}


def enrich_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    result = df.copy()
    columns = detect_columns(result)
    date_column = columns["date"]
    amount_column = columns["amount"]
    if date_column and pd.api.types.is_datetime64_any_dtype(result[date_column]):
        result["year"] = result[date_column].dt.year
        result["month"] = result[date_column].dt.to_period("M").astype(str)
        result["quarter"] = result[date_column].dt.to_period("Q").astype(str)
        result["day_of_week"] = result[date_column].dt.day_name()
    if amount_column:
        result["revenue"] = pd.to_numeric(result[amount_column], errors="coerce").fillna(0)
    return result, columns


def calculate_kpis(df: pd.DataFrame, columns: dict[str, str | None]) -> dict[str, float | int | None]:
    amount = columns["amount"]
    customer = columns["customer"]
    revenue = float(pd.to_numeric(df[amount], errors="coerce").fillna(0).sum()) if amount else None
    orders = len(df)
    customers = int(df[customer].nunique()) if customer else None
    return {
        "revenue": revenue,
        "orders": orders,
        "customers": customers,
        "average_order_value": round(revenue / orders, 2) if revenue is not None and orders else None,
        "payment_success_rate": _success_rate(df[columns["status"]]) if columns["status"] else None,
    }


def segment_metrics(df: pd.DataFrame, columns: dict[str, str | None]) -> pd.DataFrame:
    segment = columns["segment"]
    amount = columns["amount"]
    if not segment:
        return pd.DataFrame()
    grouped = df.groupby(segment, dropna=False)
    result = grouped.size().rename("records").to_frame()
    if amount:
        result["revenue"] = grouped[amount].sum().round(2)
        result["average_value"] = grouped[amount].mean().round(2)
    result["share_pct"] = (result["records"] / len(df) * 100).round(2) if len(df) else 0
    return result.sort_values("records", ascending=False).reset_index(names="segment")


def create_insights(df: pd.DataFrame, columns: dict[str, str | None], kpis: dict[str, Any], segments: pd.DataFrame) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    if kpis.get("revenue") is not None:
        insights.append({"title": "Revenue baseline established", "description": f"The dataset contains {kpis['orders']:,} records contributing {kpis['revenue']:,.2f} in observed revenue.", "severity": "info", "confidence": "high"})
    if not segments.empty and "revenue" in segments:
        top = segments.sort_values("revenue", ascending=False).iloc[0]
        insights.append({"title": "Revenue concentration", "description": f"{top['segment']} is the largest revenue segment at {top['revenue']:,.2f}. Validate whether its share is sustainable.", "severity": "watch", "confidence": "high"})
    date_column = columns["date"]
    amount = columns["amount"]
    if date_column and amount and pd.api.types.is_datetime64_any_dtype(df[date_column]):
        monthly = df.groupby(df[date_column].dt.to_period("M"))[amount].sum()
        if len(monthly) > 1 and monthly.iloc[-2] != 0:
            change = (monthly.iloc[-1] / monthly.iloc[-2] - 1) * 100
            direction = "increased" if change >= 0 else "decreased"
            insights.append({"title": "Latest period movement", "description": f"Revenue {direction} {abs(change):.1f}% versus the previous observed period.", "severity": "positive" if change >= 0 else "watch", "confidence": "medium"})
    return insights


def sql_validation(df: pd.DataFrame, columns: dict[str, str | None], kpis: dict[str, Any]) -> dict[str, Any]:
    connection = sqlite3.connect(":memory:")
    safe = df.copy()
    safe.columns = [f"c_{index}" for index, _ in enumerate(safe.columns)]
    safe.to_sql("dataset", connection, index=False, if_exists="replace")
    amount_index = list(df.columns).index(columns["amount"]) if columns["amount"] else None
    sql_value = None
    if amount_index is not None:
        sql_value = float(pd.read_sql_query(f"SELECT COALESCE(SUM(c_{amount_index}), 0) AS value FROM dataset", connection).iloc[0]["value"])
    connection.close()
    python_value = kpis.get("revenue")
    difference = abs(sql_value - python_value) if sql_value is not None and python_value is not None else None
    return {"python_revenue": python_value, "sql_revenue": sql_value, "difference": difference, "status": "MATCH" if difference is not None and difference < 0.01 else "UNAVAILABLE" if difference is None else "REVIEW"}


def run_pipeline(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        raise ValueError("The dataset is empty. Upload a file containing at least one row.")
    raw_profile = profile_dataset(df)
    cleaned, cleaning = clean_dataset(df)
    enriched, columns = enrich_dataset(cleaned)
    kpis = calculate_kpis(enriched, columns)
    segments = segment_metrics(enriched, columns)
    insights = create_insights(enriched, columns, kpis, segments)
    quality = _quality_score(raw_profile, cleaning, enriched, columns)
    return {"raw": df, "data": enriched, "profile": raw_profile, "cleaning": cleaning, "columns": columns, "kpis": kpis, "segments": segments, "insights": insights, "quality": quality, "sql": sql_validation(enriched, columns, kpis), "generated_at": datetime.now(timezone.utc).isoformat()}


def report_markdown(result: dict[str, Any], project_name: str) -> str:
    kpis = result["kpis"]
    quality = result["quality"]
    lines = [f"# {project_name} Analytics Report", "", f"Generated: {result['generated_at']}", "", "## Executive Summary", f"DataLens analysed {len(result['data']):,} records with a data quality score of {quality['score']}/100.", "", "## KPIs"]
    lines.extend(f"- {name.replace('_', ' ').title()}: {value}" for name, value in kpis.items() if value is not None)
    lines += ["", "## Insights"]
    lines.extend(f"- **{item['title']}**: {item['description']}" for item in result["insights"])
    lines += ["", "## Limitations", "Results are based only on the uploaded dataset. Missing dimensions are reported as unavailable rather than inferred."]
    return "\n".join(lines)


def _date_like(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    return not pd.api.types.is_numeric_dtype(series) and pd.to_datetime(series, format="mixed", errors="coerce").notna().mean() >= 0.8


def _success_rate(series: pd.Series) -> float:
    normalized = series.astype("string").str.lower().str.strip()
    return round(float(normalized.isin(["success", "successful", "paid", "completed", "complete"]).mean() * 100), 2)


def _quality_score(profile: dict[str, Any], cleaning: dict[str, Any], df: pd.DataFrame, columns: dict[str, str | None]) -> dict[str, Any]:
    missing_rate = float(df.isna().mean().mean() * 100) if len(df.columns) else 0
    duplicate_rate = profile["duplicates"] / profile["rows"] * 100 if profile["rows"] else 0
    invalid_amounts = int((pd.to_numeric(df[columns["amount"]], errors="coerce") < 0).sum()) if columns["amount"] else 0
    score = max(0, round(100 - missing_rate * 0.7 - duplicate_rate * 0.8 - min(invalid_amounts / max(len(df), 1) * 100, 20) * 0.5))
    status = "Passed" if score >= 90 else "Warning" if score >= 75 else "Needs Review" if score >= 50 else "Failed"
    return {"score": score, "status": status, "missing_rate": round(missing_rate, 2), "duplicate_rate": round(duplicate_rate, 2), "invalid_amounts": invalid_amounts}