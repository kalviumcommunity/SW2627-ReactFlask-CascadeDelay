-- View: vw_active_customers
-- Purpose: Provide a single definition of customer activity and
--          rolling 30-day revenue for dashboard consumption.
-- Business question: Which customers have ordered recently and
--                    how much revenue have they generated?
-- Used by: Sales and Customer Success dashboards.
--
-- SQLite implementation:
-- julianday() is used instead of MySQL DATEDIFF().

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
            julianday('now') - julianday(MAX(o.order_date))
            AS INTEGER
        )
    END AS days_since_order

FROM customers c

LEFT JOIN orders o
    ON c.customer_id = o.customer_id

GROUP BY
    c.customer_id,
    c.customer_type;
