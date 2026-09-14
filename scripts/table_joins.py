import json
import os

import pandas as pd


CUSTOMERS_FILE = "data/raw/customers.csv"
ORDERS_FILE = "data/raw/orders.csv"
OUTPUT_DIR = "output"


def load_data():
    """Load customer and order datasets."""
    df_customers = pd.read_csv(CUSTOMERS_FILE)
    df_orders = pd.read_csv(ORDERS_FILE)

    print("=" * 70)
    print("DATA LOADING")
    print("=" * 70)

    print(f"Customers: {len(df_customers)} rows")
    print(f"Orders: {len(df_orders)} rows")

    return df_customers, df_orders


def perform_left_join(df_customers, df_orders):
    """
    Merge customers with orders using a left join.

    A left join preserves every customer, including customers
    who have never placed an order.
    """

    print("\n" + "=" * 70)
    print("TASK 1: LEFT JOIN WITH ROW COUNT VALIDATION")
    print("=" * 70)

    print(f"Left: {len(df_customers)}")
    print(f"Right: {len(df_orders)}")

    df_merged = pd.merge(
        df_customers,
        df_orders,
        on="customer_id",
        how="left",
        validate="one_to_many",
    )

    print(f"Merged: {len(df_merged)}")
    print(
        f"Change: "
        f"{len(df_merged) - len(df_customers)}"
    )

    return df_merged


def detect_unmatched_keys(df_customers, df_orders):
    """Find customers without orders and orphaned orders."""

    print("\n" + "=" * 70)
    print("TASK 2: UNMATCHED KEYS")
    print("=" * 70)

    unmatched_customers = df_customers[
        ~df_customers["customer_id"].isin(
            df_orders["customer_id"]
        )
    ]

    unmatched_orders = df_orders[
        ~df_orders["customer_id"].isin(
            df_customers["customer_id"]
        )
    ]

    print(
        f"Customers without orders: "
        f"{len(unmatched_customers)}"
    )

    print(
        f"Orphaned orders: "
        f"{len(unmatched_orders)}"
    )

    unmatched_customers.to_csv(
        f"{OUTPUT_DIR}/unmatched_customers.csv",
        index=False,
    )

    unmatched_orders.to_csv(
        f"{OUTPUT_DIR}/unmatched_orders.csv",
        index=False,
    )

    print("\n✓ Unmatched records saved")

    return unmatched_customers, unmatched_orders


def compare_join_types(df_customers, df_orders):
    """Compare inner, left, and outer joins."""

    print("\n" + "=" * 70)
    print("TASK 3: JOIN TYPE COMPARISON")
    print("=" * 70)

    inner = pd.merge(
        df_customers,
        df_orders,
        on="customer_id",
        how="inner",
    )

    left = pd.merge(
        df_customers,
        df_orders,
        on="customer_id",
        how="left",
    )

    outer = pd.merge(
        df_customers,
        df_orders,
        on="customer_id",
        how="outer",
        indicator=True,
    )

    print(f"Inner: {len(inner)}")
    print(f"Left: {len(left)}")
    print(f"Outer: {len(outer)}")

    return inner, left, outer


def validate_duplication(df_merged):
    """
    Check whether the join produced expected one-to-many expansion.
    """

    print("\n" + "=" * 70)
    print("TASK 4: DUPLICATION VALIDATION")
    print("=" * 70)

    print("Merged columns:")
    print(df_merged.columns.tolist())

    key_counts = df_merged["customer_id"].value_counts()

    print(
        f"\nMax orders per customer: "
        f"{key_counts.max()}"
    )

    print(
        f"Customers represented in merged data: "
        f"{key_counts.nunique()} different order-count values"
    )

    # The relationship is expected to be one customer
    # to many orders.
    if key_counts.max() > 1:
        print(
            "✓ Multiple rows per customer are expected "
            "because customers can have multiple orders."
        )

    print("\n✓ Join key validated: customer_id")


def create_join_report(
    df_customers,
    df_orders,
    df_merged,
    unmatched_customers,
    unmatched_orders,
):
    """Create business-oriented join decision report."""

    join_report = {
        "join_type": "left",
        "left_table": "customers",
        "right_table": "orders",
        "join_key": "customer_id",
        "left_rows": len(df_customers),
        "right_rows": len(df_orders),
        "result_rows": len(df_merged),
        "unmatched_left": len(unmatched_customers),
        "unmatched_right": len(unmatched_orders),
        "reasoning": (
            "A left join was selected because the customer table "
            "is the population of interest. It preserves every "
            "customer, including customers who have not placed "
            "an order. This is important for customer analysis, "
            "retention, and identifying inactive customers."
        ),
    }

    print("\n" + "=" * 70)
    print("TASK 5: JOIN DECISION")
    print("=" * 70)

    print(json.dumps(join_report, indent=2))

    with open(
        f"{OUTPUT_DIR}/join_report.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            join_report,
            file,
            indent=2,
        )

    print("\n✓ Join report saved")

    return join_report


def validate_results(
    df_customers,
    df_orders,
    df_merged,
    unmatched_customers,
    unmatched_orders,
):
    """Run final validation checks."""

    print("\n" + "=" * 70)
    print("FINAL VALIDATION")
    print("=" * 70)

    # Every customer should remain in a left join.
    merged_customer_ids = set(
        df_merged["customer_id"].unique()
    )

    original_customer_ids = set(
        df_customers["customer_id"].unique()
    )

    assert original_customer_ids.issubset(
        merged_customer_ids
    )

    # Verify orphan orders really do not have customers.
    customer_ids = set(
        df_customers["customer_id"]
    )

    assert all(
        customer_id not in customer_ids
        for customer_id in unmatched_orders[
            "customer_id"
        ]
    )

    # Verify unmatched customers really have no orders.
    order_ids = set(
        df_orders["customer_id"]
    )

    assert all(
        customer_id not in order_ids
        for customer_id in unmatched_customers[
            "customer_id"
        ]
    )

    print("✓ All customers preserved")
    print("✓ Orphaned orders correctly identified")
    print("✓ Customers without orders correctly identified")
    print("✓ Join validation passed")


def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load
    df_customers, df_orders = load_data()

    # Task 1
    df_merged = perform_left_join(
        df_customers,
        df_orders,
    )

    # Task 2
    (
        unmatched_customers,
        unmatched_orders,
    ) = detect_unmatched_keys(
        df_customers,
        df_orders,
    )

    # Task 3
    compare_join_types(
        df_customers,
        df_orders,
    )

    # Task 4
    validate_duplication(df_merged)

    # Task 5
    create_join_report(
        df_customers,
        df_orders,
        df_merged,
        unmatched_customers,
        unmatched_orders,
    )

    # Final validation
    validate_results(
        df_customers,
        df_orders,
        df_merged,
        unmatched_customers,
        unmatched_orders,
    )

    # Save merged dataset
    df_merged.to_csv(
        f"{OUTPUT_DIR}/merged_customers_orders.csv",
        index=False,
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(
        "✓ Merged dataset: "
        "output/merged_customers_orders.csv"
    )


if __name__ == "__main__":
    main()