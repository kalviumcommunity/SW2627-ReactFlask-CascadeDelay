import os

import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine


DATABASE_PATH = "analytics.db"
OUTPUT_DIR = "interactive_charts"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# CHART 1 — DAILY REVENUE TREND
# ============================================================

revenue_df = pd.read_sql(
    """
    SELECT
        DATE(order_date) AS date,
        SUM(order_amount) AS revenue,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY DATE(order_date)
    ORDER BY DATE(order_date)
    """,
    engine
)

fig1 = go.Figure(
    data=go.Scatter(
        x=revenue_df["date"],
        y=revenue_df["revenue"],
        mode="lines+markers",
        name="Revenue",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: $%{y:,.2f}<br>"
            "<extra></extra>"
        ),
        line=dict(width=2),
        marker=dict(size=7)
    )
)

fig1.update_layout(
    title="Daily Revenue Trend",
    xaxis_title="Date",
    yaxis_title="Revenue ($)",
    hovermode="x unified",
    height=500,
    template="plotly_white"
)

fig1.write_html(
    f"{OUTPUT_DIR}/chart1_revenue_trend.html"
)


# ============================================================
# CHART 2 — PRODUCT PERFORMANCE
# ============================================================

product_df = pd.read_sql(
    """
    SELECT
        p.product_name,
        SUM(oi.quantity * oi.unit_price) AS revenue,
        COUNT(DISTINCT oi.order_id) AS order_count,
        AVG(oi.quantity * oi.unit_price) AS average_order_value
    FROM products p
    INNER JOIN order_items oi
        ON p.product_id = oi.product_id
    INNER JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.order_amount > 0
    GROUP BY
        p.product_id,
        p.product_name
    ORDER BY revenue DESC
    """,
    engine
)

fig2 = go.Figure(
    data=go.Bar(
        x=product_df["product_name"],
        y=product_df["revenue"],
        name="Revenue",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: $%{y:,.2f}<br>"
            "Orders: %{customdata[0]:,}<br>"
            "Average Order Value: $%{customdata[1]:,.2f}"
            "<extra></extra>"
        ),
        customdata=product_df[
            ["order_count", "average_order_value"]
        ].values
    )
)

fig2.update_layout(
    title="Product Performance",
    xaxis_title="Product",
    yaxis_title="Revenue ($)",
    height=500,
    template="plotly_white"
)

fig2.write_html(
    f"{OUTPUT_DIR}/chart2_product_performance.html"
)


# ============================================================
# CHART 3 — DROPDOWN METRIC SELECTOR
# ============================================================

products = product_df["product_name"].tolist()

revenue_data = product_df["revenue"].tolist()

# Use revenue * 0.25 as a demonstration profit metric.
profit_data = [
    value * 0.25
    for value in revenue_data
]

order_count_data = product_df[
    "order_count"
].tolist()


fig3 = go.Figure()

fig3.add_trace(
    go.Bar(
        x=products,
        y=revenue_data,
        name="Revenue",
        visible=True,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: $%{y:,.2f}"
            "<extra></extra>"
        )
    )
)

fig3.add_trace(
    go.Bar(
        x=products,
        y=profit_data,
        name="Profit",
        visible=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Profit: $%{y:,.2f}"
            "<extra></extra>"
        )
    )
)

fig3.add_trace(
    go.Bar(
        x=products,
        y=order_count_data,
        name="Order Count",
        visible=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Orders: %{y:,}"
            "<extra></extra>"
        )
    )
)

fig3.update_layout(
    title="Revenue by Product",
    height=500,
    template="plotly_white",

    updatemenus=[
        dict(
            active=0,
            x=0,
            y=1.15,
            xanchor="left",
            yanchor="top",

            buttons=[
                dict(
                    label="Revenue",
                    method="update",
                    args=[
                        {
                            "visible": [
                                True,
                                False,
                                False
                            ]
                        },
                        {
                            "title":
                                "Revenue by Product",
                            "yaxis": {
                                "title":
                                    "Revenue ($)"
                            }
                        }
                    ]
                ),

                dict(
                    label="Profit",
                    method="update",
                    args=[
                        {
                            "visible": [
                                False,
                                True,
                                False
                            ]
                        },
                        {
                            "title":
                                "Profit by Product",
                            "yaxis": {
                                "title":
                                    "Profit ($)"
                            }
                        }
                    ]
                ),

                dict(
                    label="Order Count",
                    method="update",
                    args=[
                        {
                            "visible": [
                                False,
                                False,
                                True
                            ]
                        },
                        {
                            "title":
                                "Order Count by Product",
                            "yaxis": {
                                "title":
                                    "Orders"
                            }
                        }
                    ]
                )
            ]
        )
    ]
)

fig3.write_html(
    f"{OUTPUT_DIR}/chart3_metric_selector.html"
)


# ============================================================
# CHART 4 — INTERACTIVE ZOOM / PAN / SELECT
# ============================================================

fig4 = go.Figure(
    data=go.Scatter(
        x=revenue_df["date"],
        y=revenue_df["revenue"],
        mode="markers",
        marker=dict(size=9),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: $%{y:,.2f}"
            "<extra></extra>"
        )
    )
)

fig4.update_layout(
    title="Interactive Revenue Exploration",
    xaxis_title="Date",
    yaxis_title="Revenue ($)",
    height=600,
    template="plotly_white",
    dragmode="zoom",
    hovermode="closest"
)

fig4.write_html(
    f"{OUTPUT_DIR}/chart4_interactive.html"
)


print("=" * 60)
print("PLOTLY CHART GENERATION COMPLETE")
print("=" * 60)

print(
    f"Revenue data points: {len(revenue_df)}"
)

print(
    f"Products: {len(product_df)}"
)

print("\nGenerated:")
print(
    "✓ chart1_revenue_trend.html"
)
print(
    "✓ chart2_product_performance.html"
)
print(
    "✓ chart3_metric_selector.html"
)
print(
    "✓ chart4_interactive.html"
)
