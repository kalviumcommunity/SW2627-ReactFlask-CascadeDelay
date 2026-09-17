import json
import os
import sys

import pandas as pd

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from kpis.kpi_functions import (
    calculate_mau,
    calculate_revenue_per_customer,
    calculate_churn_rate,
    calculate_payment_success_rate,
    calculate_customer_acquisition_cost,
    calculate_total_revenue,
    calculate_revenue_by_segment,
    calculate_revenue_by_product,
)


INPUT_FILE = "data/raw/transactions.csv"
TARGET_FILE = "kpis/kpi_validation_targets.json"


def load_data():

    df = pd.read_csv(INPUT_FILE)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"]
    )

    print("=" * 70)
    print("DATA LOADED")
    print("=" * 70)

    print(f"Rows: {len(df)}")
    print(
        f"Customers: "
        f"{df['customer_id'].nunique()}"
    )

    return df


def compute_kpis(df):

    # Use a fixed reference date for reproducibility.
    reference_date = pd.Timestamp(
        "2025-06-30"
    )

    mau = calculate_mau(
        df,
        days=30,
        reference_date=reference_date
    )

    rpc = calculate_revenue_per_customer(df)

    churn = calculate_churn_rate(
        df,
        period_days=30,
        reference_date=reference_date
    )

    payment_success = (
        calculate_payment_success_rate(df)
    )

    # Sample acquisition data for demonstration.
    marketing_spend = 15000
    new_customers = 400

    cac = calculate_customer_acquisition_cost(
        marketing_spend,
        new_customers
    )

    current_kpis = {
        "monthly_active_users": mau,
        "revenue_per_customer": rpc,
        "churn_rate": churn,
        "payment_success_rate": payment_success,
        "customer_acquisition_cost": cac,
    }

    print("\n" + "=" * 70)
    print("CURRENT KPIs")
    print("=" * 70)

    print(f"MAU: {mau:,}")
    print(f"Revenue per Customer: ${rpc:.2f}")
    print(f"Churn Rate: {churn:.1%}")
    print(
        f"Payment Success Rate: "
        f"{payment_success:.1%}"
    )
    print(f"CAC: ${cac:.2f}")

    return current_kpis


def validate_kpis(current_kpis):

    with open(
        TARGET_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        targets = json.load(file)

    validation_report = []

    for kpi_name, target_range in targets.items():

        actual = current_kpis[kpi_name]

        min_val = target_range["min"]
        max_val = target_range["max"]

        status = (
            "PASS"
            if min_val <= actual <= max_val
            else "ALERT"
        )

        validation_report.append({
            "kpi": kpi_name,
            "actual": actual,
            "target_min": min_val,
            "target_max": max_val,
            "status": status,
        })

    validation_df = pd.DataFrame(
        validation_report
    )

    print("\n" + "=" * 70)
    print("KPI TARGET VALIDATION")
    print("=" * 70)

    print(
        validation_df.to_string(
            index=False
        )
    )

    validation_df.to_csv(
        "output/kpi_validation_report.csv",
        index=False
    )

    failures = validation_df[
        validation_df["status"] == "ALERT"
    ]

    if len(failures) > 0:
        print(
            f"\n⚠️ {len(failures)} KPIs "
            "outside target range."
        )
    else:
        print(
            f"\n✓ All {len(validation_df)} KPIs "
            "within target range."
        )

    return validation_df


def create_kpi_decomposition(df):

    total_revenue = calculate_total_revenue(df)

    revenue_by_segment = (
        calculate_revenue_by_segment(df)
    )

    revenue_by_product = (
        calculate_revenue_by_product(df)
    )

    print("\n" + "=" * 70)
    print("KPI DECOMPOSITION")
    print("=" * 70)

    print(
        f"\nTotal Revenue: "
        f"${total_revenue:,.2f}"
    )

    print("\nRevenue by Customer Segment:")

    for segment, revenue in revenue_by_segment.items():
        print(
            f"  {segment}: "
            f"${revenue:,.2f}"
        )

    print("\nRevenue by Product:")

    for product, revenue in revenue_by_product.items():
        print(
            f"  {product}: "
            f"${revenue:,.2f}"
        )

    # Verify segment totals reconcile.
    segment_total = revenue_by_segment.sum()

    print(
        f"\nSegment total: "
        f"${segment_total:,.2f}"
    )

    print(
        f"Top-level total: "
        f"${total_revenue:,.2f}"
    )

    if abs(segment_total - total_revenue) < 0.01:
        print(
            "✓ Segment decomposition reconciles "
            "with total revenue."
        )

    decomposition = f"""
KPI DECOMPOSITION: TOTAL REVENUE

Level 1 - Total Revenue:
${total_revenue:,.2f}

Level 2 - Revenue by Customer Segment:
{revenue_by_segment.to_string()}

Level 3 - Revenue by Product:
{revenue_by_product.to_string()}

Validation:
Segment revenue sums to total revenue:
${segment_total:,.2f}

The decomposition allows stakeholders to move
from the overall KPI to the customer segments
and products responsible for the result.
"""

    with open(
        "output/kpi_decomposition.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(decomposition)

    print(
        "\n✓ Decomposition saved to "
        "output/kpi_decomposition.txt"
    )


def main():

    os.makedirs(
        "output",
        exist_ok=True
    )

    df = load_data()

    current_kpis = compute_kpis(df)

    validate_kpis(
        current_kpis
    )

    create_kpi_decomposition(df)

    print("\n" + "=" * 70)
    print("KPI ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()