import pandas as pd

from datalens.core import run_pipeline


def sample_data():
    return pd.DataFrame({
        "transaction_id": [1, 2, 2, 3],
        "customer_id": [10, 10, 10, 11],
        "transaction_date": ["2025-01-01", "2025-01-02", "2025-01-02", "2025-02-01"],
        "amount": [100, 50, 50, 200],
        "customer_type": ["SMB", "SMB", "SMB", "Enterprise"],
        "payment_status": ["success", "success", "success", "failed"],
    })


def test_pipeline_preserves_raw_and_cleans_duplicates():
    result = run_pipeline(sample_data())
    assert len(result["raw"]) == 4
    assert len(result["data"]) == 3
    assert result["cleaning"]["duplicates_removed"] == 1


def test_kpis_and_sql_validation_reconcile():
    result = run_pipeline(sample_data())
    assert result["kpis"]["revenue"] == 350.0
    assert result["sql"]["status"] == "MATCH"
    assert result["kpis"]["customers"] == 2


def test_missing_capabilities_are_explicit():
    result = run_pipeline(pd.DataFrame({"name": ["A", "B"], "score": [1, 2]}))
    assert result["kpis"]["revenue"] is None
    assert result["segments"].empty