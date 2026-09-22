-- Table: agg_daily_metrics
-- Purpose: Store pre-aggregated daily revenue metrics.
-- Business grain: One row per day.
-- Used by: Sales and Operations dashboards.
--
-- updated_at records when the aggregation was generated.

CREATE TABLE IF NOT EXISTS agg_daily_metrics (
    aggregation_date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    row_count INTEGER NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
