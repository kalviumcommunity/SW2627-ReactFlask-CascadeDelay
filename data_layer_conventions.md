# Clean Data Layer Naming Conventions

## Views

All reusable SQL views use the `vw_` prefix.

Pattern:

    vw_[business_entity]_[metric]

Examples:

- `vw_active_customers`
- `vw_product_performance`

The `vw_` prefix makes it immediately clear that the object is a
logical view rather than a physical table.

## Pre-Aggregated Tables

All pre-aggregated tables use the `agg_` prefix.

Pattern:

    agg_[grain]_[subject]

Example:

- `agg_daily_metrics`

The name identifies that the table contains pre-computed data and
also communicates its time grain.

## Aggregated Table Columns

Pre-aggregated tables should include:

- A date/time grain column
- A metric name
- A metric value
- A row count for validation
- An `updated_at` timestamp

## Benefits

Consistent naming:

- Makes object types immediately identifiable
- Prevents naming conflicts across teams
- Gives dashboards predictable data sources
- Makes SQL easier to understand
- Reduces metric-definition drift
- Creates a clear separation between raw data and the clean data layer
