import json
import os
from datetime import datetime

import pandas as pd


def capture_dtypes(df):
    """Capture the data types of all columns."""
    return {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }


def enforce_date_type(df):
    """Convert transaction_date from string to datetime."""
    try:
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            format="%Y-%m-%d"
        ).astype("datetime64[ns]")

        return True, "transaction_date converted to datetime"

    except Exception as error:
        return False, f"Date conversion failed: {error}"


def enforce_currency_type(df):
    """Remove currency symbols and convert amount to float."""
    try:
        df["amount"] = (
            df["amount"]
            .astype(str)
            .str.replace(r"[$,]", "", regex=True)
        )

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="raise"
        )

        return True, "amount converted to float"

    except Exception as error:
        return False, f"Currency conversion failed: {error}"


def enforce_boolean_type(df):
    """Convert 0/1 values to boolean."""
    try:
        df["is_active"] = df["is_active"].map({
            0: False,
            1: True
        })

        if df["is_active"].isna().any():
            return False, "Boolean conversion failed: unexpected values found"

        df["is_active"] = df["is_active"].astype(bool)

        return True, "is_active converted to boolean"

    except Exception as error:
        return False, f"Boolean conversion failed: {error}"


def validate_types(df):
    """Validate that all expected types were enforced."""
    expected_types = {
        "transaction_date": "datetime64[ns]",
        "amount": "float64",
        "is_active": "bool"
    }

    results = {}

    for column, expected_type in expected_types.items():
        actual_type = str(df[column].dtype)

        results[column] = {
            "expected": expected_type,
            "actual": actual_type,
            "passed": actual_type == expected_type
        }

    return results


def generate_type_report(filepath):
    """Load dataset, enforce types, validate conversions, and save report."""

    df = pd.read_csv(filepath)

    # Capture types before conversion
    dtypes_before = capture_dtypes(df)

    report = {
        "timestamp": datetime.now().isoformat(),
        "filepath": filepath,
        "dtypes_before": dtypes_before,
        "conversions": {}
    }

    # Date conversion
    passed, message = enforce_date_type(df)

    report["conversions"]["transaction_date"] = {
        "passed": passed,
        "message": message
    }

    if not passed:
        report["ready_for_analysis"] = False
        save_report(report)
        return report

    # Currency conversion
    passed, message = enforce_currency_type(df)

    report["conversions"]["amount"] = {
        "passed": passed,
        "message": message
    }

    if not passed:
        report["ready_for_analysis"] = False
        save_report(report)
        return report

    # Boolean conversion
    passed, message = enforce_boolean_type(df)

    report["conversions"]["is_active"] = {
        "passed": passed,
        "message": message
    }

    if not passed:
        report["ready_for_analysis"] = False
        save_report(report)
        return report

    # Capture types after conversion
    report["dtypes_after"] = capture_dtypes(df)

    # Validate final types
    report["type_validation"] = validate_types(df)

    # Overall result
    report["ready_for_analysis"] = all(
        item["passed"]
        for item in report["type_validation"].values()
    )

    # Save report
    save_report(report)

    return report


def save_report(report):
    """Save the type enforcement report."""
    os.makedirs("output", exist_ok=True)

    with open(
        "output/type_enforcement_report.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2, default=str)


if __name__ == "__main__":

    DATASET_PATH = "data/raw/sample.csv"

    result = generate_type_report(DATASET_PATH)

    print(json.dumps(result, indent=2, default=str))