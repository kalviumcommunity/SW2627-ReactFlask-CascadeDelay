import time

import pandas as pd
from sqlalchemy import create_engine, text


DATABASE_PATH = "analytics.db"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}"
)


def execute_sql(sql):
    """Execute a SQL statement against the analytics database."""
    with engine.begin() as connection:
        connection.execute(text(sql))


def create_views():
    """Create the reusable business metric views."""

    # Drop existing views so the script can be rerun.
    execute_sql(
        "DROP VIEW IF EXISTS vw_active_customers"
    )

    execute_sql(
        "DROP VIEW IF EXISTS vw_product_performance"
    )

    # View 1: customer activity and rolling revenue.
    active_customers_sql = """
    CREATE VIEW vw_active_customers AS
    SELECT
        c.customer_id,
        c.customer_type AS segment,

        COUNT(DISTINCT CASE
            WHEN o.order_date >= date('now', '-30 days')
            THEN o.order_id
        END) AS order_count_30d,

        COALESCE(
            SUM(
                CASE
                    WHEN o.order_date >= date('now', '-30 days')
                    THEN o.order_amount
                    ELSE 0
                END
            ),
            0
        ) AS revenue_30d,

        MAX(o.order_date) AS last_order_date,

        CASE
            WHEN MAX(o.order_date) IS NULL THEN NULL
            ELSE CAST(
                julianday('now')
                - julianday(MAX(o.order_date))
                AS INTEGER
            )
        END AS days_since_order

    FROM customers c

    LEFT JOIN orders o
        ON c.customer_id = o.customer_id

    GROUP BY
        c.customer_id,
        c.customer_type
    """

    execute_sql(active_customers_sql)

    # View 2: product performance.
    product_performance_sql = """
    CREATE VIEW vw_product_performance AS
    SELECT
        p.product_id,
        p.product_name,
        COUNT(DISTINCT oi.order_id) AS order_count,
        SUM(oi.quantity) AS units_sold,
        SUM(
            oi.quantity * oi.unit_price
        ) AS product_revenue,
        AVG(oi.unit_price) AS average_unit_price

    FROM products p

    INNER JOIN order_items oi
        ON p.product_id = oi.product_id

    INNER JOIN orders o
        ON oi.order_id = o.order_id

    WHERE o.order_amount > 0

    GROUP BY
        p.product_id,
        p.product_name
    """

    execute_sql(product_performance_sql)

    print("✓ Both views created")


def create_aggregation_table():
    """Create and populate the daily pre-aggregated metrics table."""

    execute_sql(
        "DROP TABLE IF EXISTS agg_daily_metrics"
    )

    create_table_sql = """
    CREATE TABLE agg_daily_metrics (
        aggregation_date DATE NOT NULL,
        metric_name VARCHAR(100) NOT NULL,
        metric_value NUMERIC NOT NULL,
        row_count INTEGER NOT NULL,
        updated_at TIMESTAMP NOT NULL
    )
    """

    execute_sql(create_table_sql)

    populate_sql = """
    INSERT INTO agg_daily_metrics
    SELECT
        DATE(order_date) AS aggregation_date,
        'total_revenue' AS metric_name,
        SUM(order_amount) AS metric_value,
        COUNT(*) AS row_count,
        CURRENT_TIMESTAMP AS updated_at
    FROM orders
    WHERE order_amount > 0
    GROUP BY DATE(order_date)
    """

    execute_sql(populate_sql)

    print("✓ Daily aggregation table created and populated")


def validate_views():
    """Query both views and validate their output."""

    active_customers = pd.read_sql(
        """
        SELECT *
        FROM vw_active_customers
        LIMIT 10
        """,
        engine
    )

    product_performance = pd.read_sql(
        """
        SELECT *
        FROM vw_product_performance
        ORDER BY product_revenue DESC
        LIMIT 10
        """,
        engine
    )

    print("\nVIEW 1: ACTIVE CUSTOMERS")
    print(
        "Columns:",
        active_customers.columns.tolist()
    )
    print(active_customers.to_string(index=False))

    print("\nVIEW 2: PRODUCT PERFORMANCE")
    print(
        "Columns:",
        product_performance.columns.tolist()
    )
    print(product_performance.to_string(index=False))


def validate_aggregation():
    """Query the pre-aggregated table and test its timestamp."""

    agg_data = pd.read_sql(
        """
        SELECT
            aggregation_date,
            metric_name,
            metric_value,
            row_count,
            updated_at
        FROM agg_daily_metrics
        ORDER BY aggregation_date DESC
        LIMIT 10
        """,
        engine
    )

    print("\nPRE-AGGREGATED DAILY METRICS")
    print(agg_data.to_string(index=False))

    assert len(agg_data) > 0

    assert agg_data["updated_at"].notna().all()

    print("\n✓ updated_at validation passed")


def simulate_dashboard_queries():
    """Demonstrate how dashboards can consume the clean data layer."""

    print("\n" + "=" * 60)
    print("DASHBOARD QUERY SIMULATION")
    print("=" * 60)

    # Query active customer view.
    active = pd.read_sql(
        """
        SELECT
            customer_id,
            segment,
            revenue_30d,
            days_since_order
        FROM vw_active_customers
        WHERE days_since_order <= 30
        ORDER BY revenue_30d DESC
        LIMIT 20
        """,
        engine
    )

    print("\nTop active customers:")
    print(active.to_string(index=False))

    # Query product performance view.
    products = pd.read_sql(
        """
        SELECT
            product_id,
            product_name,
            units_sold,
            product_revenue
        FROM vw_product_performance
        ORDER BY product_revenue DESC
        LIMIT 10
        """,
        engine
    )

    print("\nTop products:")
    print(products.to_string(index=False))

    # Query pre-aggregated table.
    start = time.time()

    daily_metrics = pd.read_sql(
        """
        SELECT
            aggregation_date,
            metric_name,
            metric_value
        FROM agg_daily_metrics
        ORDER BY aggregation_date DESC
        LIMIT 30
        """,
        engine
    )

    elapsed = (
        time.time() - start
    ) * 1000

    print("\nDaily metrics:")
    print(daily_metrics.to_string(index=False))

    print(
        f"\nPre-aggregated query time: "
        f"{elapsed:.2f} ms"
    )

    # Revenue by customer segment.
    segment = pd.read_sql(
        """
        SELECT
            segment,
            COUNT(*) AS customer_count,
            SUM(revenue_30d) AS total_segment_revenue,
            AVG(revenue_30d) AS avg_customer_revenue
        FROM vw_active_customers
        GROUP BY segment
        ORDER BY total_segment_revenue DESC
        """,
        engine
    )

    print("\nRevenue by segment:")
    print(segment.to_string(index=False))


def main():

    print("=" * 60)
    print("CLEAN DATA LAYER")
    print("=" * 60)

    create_views()

    create_aggregation_table()

    validate_views()

    validate_aggregation()

    simulate_dashboard_queries()

    print("\n" + "=" * 60)
    print("✓ ALL DATA LAYER TASKS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
