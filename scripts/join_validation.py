import pandas as pd
from sqlalchemy import create_engine, text


DATABASE_PATH = "analytics.db"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}"
)


def execute_query(query):
    """Execute a SQL query and return the result as a DataFrame."""
    return pd.read_sql(text(query), engine)


def main():

    print("=" * 70)
    print("JOIN VALIDATION ANALYSIS")
    print("=" * 70)

    # ============================================================
    # TASK 1 — LEFT JOIN WITH ROW COUNT VALIDATION
    # ============================================================

    customers = execute_query(
        """
        SELECT *
        FROM customers
        """
    )

    orders = execute_query(
        """
        SELECT *
        FROM orders
        """
    )

    customers_count = len(customers)
    orders_count = len(orders)

    print("\nTASK 1: BASE ROW COUNTS")
    print(f"Customers: {customers_count}")
    print(f"Orders:    {orders_count}")

    left_query = """
        SELECT
            c.customer_id,
            c.customer_type,
            COUNT(DISTINCT o.order_id) AS order_count,
            COALESCE(SUM(o.order_amount), 0) AS total_spent
        FROM customers c
        LEFT JOIN orders o
            ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.customer_type
        ORDER BY total_spent DESC
    """

    left = execute_query(left_query)

    print("\nLEFT JOIN:")
    print(f"Before: {customers_count} customers")
    print(f"After:  {len(left)} rows")

    change = len(left) - customers_count
    percentage = (
        change / customers_count * 100
        if customers_count
        else 0
    )

    print(
        f"Change: {change} ({percentage:.1f}%)"
    )

    multiplication_factor = (
        orders_count / customers_count
        if customers_count
        else 0
    )

    print(
        f"Orders per customer: "
        f"{multiplication_factor:.2f}"
    )

    print(
        "\nDecision: The grouped LEFT JOIN returns one row "
        "per customer, so it does not multiply customers "
        "in the final result. Customers without orders are "
        "still retained."
    )

    # ============================================================
    # TASK 2 — UNMATCHED KEYS
    # ============================================================

    no_orders_query = """
        SELECT
            c.customer_id,
            c.customer_type,
            c.signup_date
        FROM customers c
        LEFT JOIN orders o
            ON c.customer_id = o.customer_id
        WHERE o.order_id IS NULL
        ORDER BY c.signup_date
    """

    orphaned_query = """
        SELECT
            o.order_id,
            o.customer_id,
            o.order_date
        FROM orders o
        LEFT JOIN customers c
            ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        ORDER BY o.order_date
    """

    no_orders = execute_query(no_orders_query)
    orphaned = execute_query(orphaned_query)

    no_orders_percentage = (
        len(no_orders) / customers_count * 100
        if customers_count
        else 0
    )

    print("\nTASK 2: UNMATCHED KEYS")

    print(
        f"Customers without orders: "
        f"{len(no_orders)} "
        f"({no_orders_percentage:.1f}%)"
    )

    print(
        f"Orphaned orders: {len(orphaned)}"
    )

    if len(orphaned) > 0:
        print(
            "⚠ Orphaned records found — "
            "customer_id mismatch requires investigation."
        )
    else:
        print(
            "✓ No orphaned orders found."
        )

    # ============================================================
    # TASK 3 — COMPARE JOIN TYPES
    # ============================================================

    inner_query = """
        SELECT
            c.customer_id,
            o.order_id,
            o.order_amount
        FROM customers c
        INNER JOIN orders o
            ON c.customer_id = o.customer_id
    """

    left_detail_query = """
        SELECT
            c.customer_id,
            o.order_id,
            o.order_amount
        FROM customers c
        LEFT JOIN orders o
            ON c.customer_id = o.customer_id
    """

    full_query = """
        SELECT
            c.customer_id,
            o.order_id,
            o.order_amount
        FROM customers c
        FULL OUTER JOIN orders o
            ON c.customer_id = o.customer_id
    """

    inner = execute_query(inner_query)
    left_detail = execute_query(left_detail_query)
    full = execute_query(full_query)

    print("\nTASK 3: JOIN TYPE COMPARISON")

    print(
        f"INNER: {len(inner)} rows "
        "(only matched records)"
    )

    print(
        f"LEFT:  {len(left_detail)} rows "
        "(all customers + matched orders)"
    )

    print(
        f"FULL:  {len(full)} rows "
        "(all customers + all orders)"
    )

    assert len(left_detail) >= len(inner)
    assert len(full) >= len(inner)

    print(
        "✓ Join relationship row counts validated."
    )

    # ============================================================
    # TASK 4 — MULTI-TABLE JOIN
    # ============================================================

    multi_query = """
        SELECT
            c.customer_id,
            c.customer_type,
            o.order_id,
            o.order_date,
            oi.product_id,
            p.product_name,
            oi.quantity,
            oi.unit_price,
            (oi.quantity * oi.unit_price) AS line_total
        FROM customers c
        LEFT JOIN orders o
            ON c.customer_id = o.customer_id
        LEFT JOIN order_items oi
            ON o.order_id = oi.order_id
        LEFT JOIN products p
            ON oi.product_id = p.product_id
        WHERE c.customer_type = 'Enterprise'
        ORDER BY o.order_date DESC
    """

    multi_result = execute_query(multi_query)

    print("\nTASK 4: MULTI-TABLE JOIN")

    print(
        f"Enterprise joined rows: "
        f"{len(multi_result)}"
    )

    # Validate the multi-table join against
    # Enterprise order items only.
    expected_query = """
        SELECT
            SUM(oi.quantity * oi.unit_price) AS expected_total
        FROM order_items oi
        INNER JOIN orders o
            ON oi.order_id = o.order_id
        INNER JOIN customers c
            ON o.customer_id = c.customer_id
        WHERE c.customer_type = 'Enterprise'
    """

    expected = execute_query(expected_query)

    expected_total = expected.iloc[0]["expected_total"]

    if pd.isna(expected_total):
        expected_total = 0

    actual_total = multi_result["line_total"].sum()

    difference = abs(
        actual_total - expected_total
    )

    print(
        f"Joined total:   ${actual_total:.2f}"
    )

    print(
        f"Expected total: ${expected_total:.2f}"
    )

    print(
        f"Difference:      ${difference:.2f}"
    )

    assert difference < 0.01, (
        "Unexpected duplication in multi-table join!"
    )

    print(
        "✓ Multi-table join validated — "
        "no unexpected duplication."
    )

    # ============================================================
    # TASK 5 — DOCUMENT JOIN DECISIONS
    # ============================================================

    documentation = f"""
JOIN STRATEGY DOCUMENTATION

Base tables:
- customers: {customers_count} rows
- orders: {orders_count} rows
- order_items: detailed order line items
- products: product reference data

Decision 1: customers LEFT JOIN orders
--------------------------------------------------
Purpose:
Get all customers together with their order history.

Base customers:
{customers_count}

Orders:
{orders_count}

Grouped result:
{len(left)} customers

Orders per customer:
{multiplication_factor:.2f}

Why LEFT JOIN:
Every customer must remain in the customer-level
analysis, including customers who have never ordered.

Business use:
Customer lifetime value, segmentation, and customer
activity analysis.

Decision 2: orders LEFT JOIN order_items
--------------------------------------------------
Purpose:
Connect each order to its detailed line items.

The relationship is one-to-many because one order can
contain multiple products.

Business use:
Product revenue, inventory analysis, and order detail.

Risk:
Aggregating order-level values after joining to multiple
line items can duplicate those order-level values.

Decision 3: orders + order_items + products
--------------------------------------------------
Purpose:
Create a complete order-line-product dataset.

The join expands from orders to order items because an
order can contain multiple items.

Business use:
Product-level revenue and product performance.

Validation:
Enterprise line totals were compared with an independent
SQL aggregation.

Difference:
${difference:.2f}

Result:
The multi-table join passed the duplication check.

Unmatched-key analysis:
- Customers without orders: {len(no_orders)}
- Orphaned orders: {len(orphaned)}

JOIN TYPE MEANINGS
--------------------------------------------------
INNER JOIN:
Returns only records with matching keys in both tables.

LEFT JOIN:
Returns every record from the left table and matching
records from the right table.

FULL OUTER JOIN:
Returns every record from both tables, including
unmatched records.

Validation principle:
Row counts must be checked before and after every join.
Unexpected increases can indicate one-to-many relationships
or accidental duplication.
"""

    print(documentation)

    # Save documentation
    with open(
        "output/join_strategy_documentation.txt",
        "w"
    ) as file:
        file.write(documentation)

    # Save summary
    summary = pd.DataFrame(
        {
            "join_type": [
                "INNER",
                "LEFT",
                "FULL OUTER"
            ],
            "row_count": [
                len(inner),
                len(left_detail),
                len(full)
            ]
        }
    )

    summary.to_csv(
        "output/join_comparison.csv",
        index=False
    )

    print("\n" + "=" * 70)
    print("✓ ALL JOIN VALIDATION TASKS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()



