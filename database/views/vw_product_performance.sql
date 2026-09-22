-- View: vw_product_performance
-- Purpose: Calculate product-level sales performance from order items.
-- Business question: Which products generate the most revenue and units?
-- Used by: Operations and Product dashboards.
--
-- The view joins products, order_items, and orders so that
-- product performance is calculated only from valid orders.

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
    p.product_name;
