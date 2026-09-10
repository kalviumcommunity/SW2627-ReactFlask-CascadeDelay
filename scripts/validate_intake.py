import json
import os
from datetime import datetime

import chardet
import pandas as pd


def validate_file_exists(filepath):
    """Check if file exists and is non-empty."""
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"

    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"

    return True, "File exists and has content"


def validate_file_format(filepath, allowed_formats=None):
    """Check if file extension is supported."""
    if allowed_formats is None:
        allowed_formats = ["csv", "json", "xlsx"]

    extension = filepath.split(".")[-1].lower()

    if extension not in allowed_formats:
        return (
            False,
            f"Unsupported format: {extension}. Allowed: {allowed_formats}",
        )

    return True, f"Format valid: {extension}"


def validate_schema(df, expected_columns):
    """Validate that DataFrame has all expected columns."""
    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)

    issues = []

    if missing:
        issues.append(f"Missing columns: {sorted(missing)}")

    if extra:
        issues.append(f"Unexpected columns: {sorted(extra)}")

    if not issues:
        return True, f"Schema valid: {len(df.columns)} columns present"

    return False, " | ".join(issues)


def detect_encoding(filepath):
    """Detect file encoding with confidence."""
    with open(filepath, "rb") as file:
        result = chardet.detect(file.read(10000))

    encoding = result.get("encoding") or "unknown"
    confidence = result.get("confidence", 0)

    return encoding, f"Detected: {encoding} (confidence: {confidence:.1%})"


def capture_dataset_stats(filepath, df):
    """Capture row count, column count, and file size."""
    file_size_bytes = os.path.getsize(filepath)

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 5),
        "bytes": file_size_bytes,
    }


def generate_intake_report(filepath, expected_columns):
    """Generate complete intake validation report."""

    report = {
        "timestamp": datetime.now().isoformat(),
        "filepath": filepath,
        "validations": {},
    }

    # Task 1: Check file existence
    file_exists, message = validate_file_exists(filepath)

    report["validations"]["file_exists"] = {
        "passed": file_exists,
        "message": message,
    }

    if not file_exists:
        return report

    # Task 1: Check file format
    format_valid, message = validate_file_format(filepath)

    report["validations"]["format"] = {
        "passed": format_valid,
        "message": message,
    }

    if not format_valid:
        return report

    # Task 3: Detect encoding before reading the file
    encoding, message = detect_encoding(filepath)

    encoding_valid = encoding.lower().replace("-", "") in {
        "utf8",
        "ascii",
    }

    report["validations"]["encoding"] = {
        "passed": encoding_valid,
        "encoding": encoding,
        "message": message,
    }

    # Read CSV
    try:
        df = pd.read_csv(filepath, encoding=encoding)
    except Exception as error:
        report["validations"]["ingestion"] = {
            "passed": False,
            "message": f"Unable to read dataset: {error}",
        }
        return report

    report["validations"]["ingestion"] = {
        "passed": True,
        "message": "Dataset loaded successfully",
    }

    # Task 2: Validate schema
    schema_valid, message = validate_schema(df, expected_columns)

    report["validations"]["schema"] = {
        "passed": schema_valid,
        "message": message,
    }

    # Task 4: Capture dataset statistics
    report["statistics"] = capture_dataset_stats(filepath, df)

    # Overall result
    report["ready_for_analysis"] = all(
        validation.get("passed", False)
        for validation in report["validations"].values()
    )

    # Task 5: Save report
    os.makedirs("output", exist_ok=True)

    with open("output/intake_report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return report


if __name__ == "__main__":
    DATASET_PATH = "data/raw/sample.csv"

    EXPECTED_COLUMNS = [
        "customer_id",
        "customer_name",
        "transaction_amount",
        "transaction_date",
    ]

    result = generate_intake_report(
        DATASET_PATH,
        EXPECTED_COLUMNS,
    )

    print(json.dumps(result, indent=2))