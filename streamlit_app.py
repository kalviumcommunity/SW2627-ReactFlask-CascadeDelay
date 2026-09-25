import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine


DATABASE_PATH = "analytics.db"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}"
)


st.set_page_config(
    page_title="Interactive Sales Dashboard",
    layout="wide"
)

st.title("📊 Interactive Sales Dashboard")

st.markdown(
    """
    Explore sales performance using interactive Plotly charts.
    Use the filters and chart interactions to investigate the data.
    """
)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_sql(
    """
    SELECT
        order_id,
        order_date,
        customer_id,
        order_amount
    FROM orders
    ORDER BY order_date
    """,
    engine
)

df["order_date"] = pd.to_datetime(
    df["order_date"]
)


# ============================================================
# SIDEBAR FILTER
# ============================================================

st.sidebar.header("Filters")

min_amount = st.sidebar.slider(
    "Minimum Order Amount",
    min_value=0.0,
    max_value=float(df["order_amount"].max()),
    value=0.0,
    step=10.0
)

filtered_df = df[
    df["order_amount"] >= min_amount
]


st.write(
    f"Showing {len(filtered_df):,} orders "
    f"≥ ${min_amount:,.2f}"
)


# ============================================================
# REVENUE TREND
# ============================================================

daily = (
    filtered_df
    .assign(
        date=filtered_df["order_date"].dt.date
    )
    .groupby("date")
    .agg(
        revenue=("order_amount", "sum"),
        order_count=("order_id", "count")
    )
    .reset_index()
)


fig = go.Figure(
    data=go.Scatter(
        x=daily["date"],
        y=daily["revenue"],
        mode="lines+markers",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: $%{y:,.2f}"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    title="Daily Revenue Trend",
    xaxis_title="Date",
    yaxis_title="Revenue ($)",
    hovermode="x unified",
    height=500
)


st.plotly_chart(
    fig,
    width="stretch"
)


# ============================================================
# SUMMARY METRICS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Orders",
        f"{len(filtered_df):,}"
    )

with col2:
    st.metric(
        "Revenue",
        f"${filtered_df['order_amount'].sum():,.2f}"
    )

with col3:
    average_order = (
        filtered_df["order_amount"].mean()
        if len(filtered_df) > 0
        else 0
    )

    st.metric(
        "Average Order Value",
        f"${average_order:,.2f}"
    )


# ============================================================
# DATA TABLE
# ============================================================

st.subheader("Filtered Orders")

st.dataframe(
    filtered_df[
        [
            "order_date",
            "customer_id",
            "order_amount"
        ]
    ],
    width="stretch"
)
