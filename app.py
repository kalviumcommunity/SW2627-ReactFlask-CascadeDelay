"""DataLens: From Dataset to Insights."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from datalens.core import load_dataset, report_markdown, run_pipeline


ROOT = Path(__file__).resolve().parent
DEMO_FILE = ROOT / "data" / "raw" / "transactions.csv"

st.set_page_config(page_title="DataLens", page_icon="DL", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --paper: #f4f0e8; --ink: #18202b; --muted: #68717d; --blue: #2457d6; --red: #ed5b4f; --yellow: #f2c94c; --line: #18202b; }
.stApp { background: var(--paper); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #202936; border-right: 3px solid var(--line); }
[data-testid="stSidebar"] * { color: #f8f4ea; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #c0c7d0; }
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
h1, h2, h3 { color: var(--ink); font-weight: 700; letter-spacing: 0; }
h1 { font-size: clamp(2.2rem, 4vw, 4.4rem); line-height: .95; }
h2 { font-size: 1.55rem; border-bottom: 3px solid var(--line); padding-bottom: .45rem; }
h3 { font-size: 1.1rem; }
.dl-kicker { color: var(--red); font-family: 'DM Mono', monospace; font-weight: 500; letter-spacing: .08em; text-transform: uppercase; font-size: .72rem; }
[data-testid="stMetric"] { background: #fffdf7; border: 3px solid var(--line); box-shadow: 5px 5px 0 var(--line); padding: 16px; border-radius: 0; min-height: 112px; }
[data-testid="stMetricLabel"] { color: var(--muted); font-family: 'DM Mono', monospace; text-transform: uppercase; font-size: .7rem; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: 1.8rem; }
.stButton > button, .stDownloadButton > button { border: 3px solid var(--line); border-radius: 0; box-shadow: 4px 4px 0 var(--line); font-weight: 700; color: var(--ink); background: var(--yellow); }
.stButton > button:hover, .stDownloadButton > button:hover { color: var(--ink); border-color: var(--line); transform: translate(2px, 2px); box-shadow: 2px 2px 0 var(--line); }
[data-testid="stFileUploader"] { border: 3px dashed #aeb7c2; border-radius: 0; background: #293341; }
[data-testid="stProgressBar"] > div > div { background: var(--blue); }
[data-testid="stDataFrame"] { border: 3px solid var(--line); }
.stAlert { border-radius: 0; border: 3px solid var(--line); }
.block-container { padding-top: 3rem; padding-bottom: 4rem; }
</style>""", unsafe_allow_html=True)


def _load_result() -> dict:
    if "result" not in st.session_state:
        st.session_state.result = run_pipeline(load_dataset(DEMO_FILE))
        st.session_state.filename = "transactions.csv (demo)"
    return st.session_state.result


def _metric(label: str, value, prefix: str = ""):
    if value is None:
        st.metric(label, "Unavailable")
    elif isinstance(value, float):
        st.metric(label, f"{prefix}{value:,.2f}")
    else:
        st.metric(label, f"{prefix}{value:,}")


def main() -> None:
    result = _load_result()
    with st.sidebar:
        st.markdown("<div class='dl-kicker'>Analytics workspace</div>", unsafe_allow_html=True)
        st.title("DataLens")
        st.caption("From Dataset to Insights")
        uploaded = st.file_uploader("Upload CSV or JSON", type=["csv", "json"])
        if uploaded and st.button("Process dataset", type="primary", width="stretch"):
            try:
                st.session_state.result = run_pipeline(load_dataset(uploaded.getvalue(), uploaded.name))
                st.session_state.filename = uploaded.name
                st.rerun()
            except (ValueError, pd.errors.ParserError) as error:
                st.error(str(error))
        if st.button("Restore demo dataset", width="stretch"):
            st.session_state.result = run_pipeline(load_dataset(DEMO_FILE))
            st.session_state.filename = "transactions.csv (demo)"
            st.rerun()
        st.divider()
        page = st.radio("Workspace", ["Overview", "Dataset", "Data Quality", "Analysis", "Segmentation", "SQL Validation", "Insights", "Reports", "Alerts", "Settings"], label_visibility="collapsed")
        st.caption(f"Source: {st.session_state.filename}")

    st.markdown("<div class='dl-kicker'>Data product / live workspace</div>", unsafe_allow_html=True)
    st.title(page)
    if page == "Overview":
        _overview(result)
    elif page == "Dataset":
        _dataset(result)
    elif page == "Data Quality":
        _quality(result)
    elif page == "Analysis":
        _analysis(result)
    elif page == "Segmentation":
        _segmentation(result)
    elif page == "SQL Validation":
        _sql(result)
    elif page == "Insights":
        _insights(result)
    elif page == "Reports":
        _reports(result)
    elif page == "Alerts":
        _alerts(result)
    else:
        st.info("Settings are local to this workspace. Uploads are processed in memory and the raw source is never modified.")
        st.json({"demo_dataset": str(DEMO_FILE.relative_to(ROOT)), "supported_formats": ["CSV", "JSON"], "database": "SQLite in-memory validation"})


def _overview(result):
    kpis = result["kpis"]
    cols = st.columns(5)
    for column, (label, value) in zip(cols, [("Revenue", kpis["revenue"]), ("Orders", kpis["orders"]), ("Customers", kpis["customers"]), ("Avg order", kpis["average_order_value"]), ("Payment success", kpis["payment_success_rate"])]):
        with column:
            _metric(label, value)
    st.subheader("Pipeline status")
    st.progress(1.0, text="Dataset  •  Quality  •  Analysis  •  Validation  •  Insights  •  Report")
    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Revenue trend")
        date_column, amount_column = result["columns"]["date"], result["columns"]["amount"]
        if date_column and amount_column:
            trend = result["data"].groupby(result["data"][date_column].dt.to_period("M").astype(str), as_index=False)[amount_column].sum()
            trend.columns = ["period", "revenue"]
            chart = px.area(trend, x="period", y="revenue", template="simple_white")
            chart.update_layout(paper_bgcolor="#fffdf7", plot_bgcolor="#fffdf7", font_color="#18202b", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(chart, width="stretch")
        else:
            st.info("A date and amount column are required for trend analysis.")
    with right:
        st.subheader("Trust signal")
        st.metric("Data quality", f"{result['quality']['score']}/100", result["quality"]["status"])
        st.write("The score combines missing values, duplicates, and invalid amount ranges. It is a review signal, not a guarantee of correctness.")


def _dataset(result):
    profile = result["profile"]
    cols = st.columns(6)
    for column, (label, value) in zip(cols, [("Rows", profile["rows"]), ("Columns", profile["columns"]), ("Memory", f"{profile['memory_mb']} MB"), ("Missing", f"{sum(item['missing'] for item in profile['column_profile']):,}"), ("Duplicates", profile["duplicates"]), ("Dates", profile["date_columns"])]):
        with column:
            st.metric(label, value)
    st.subheader("Preview")
    st.dataframe(result["data"].head(100), width="stretch", height=420)
    st.subheader("Data dictionary")
    st.dataframe(pd.DataFrame(result["profile"]["column_profile"]), width="stretch")


def _quality(result):
    quality = result["quality"]
    left, right = st.columns([1, 2])
    with left:
        st.metric("Quality score", f"{quality['score']}/100")
        st.metric("Status", quality["status"])
    with right:
        st.write({"Missing rate": f"{quality['missing_rate']}%", "Duplicate rate": f"{quality['duplicate_rate']}%", "Invalid amount rows": quality["invalid_amounts"]})
        st.success(f"Cleaning preserved the raw source and produced {result['cleaning']['rows_after']:,} analysis rows.")
    st.subheader("Column-level checks")
    st.dataframe(pd.DataFrame(result["profile"]["column_profile"]), width="stretch")


def _analysis(result):
    data = result["data"]
    numeric = data.select_dtypes(include="number").columns.tolist()
    if not numeric:
        st.info("No numeric columns are available for distribution analysis.")
        return
    selected = st.selectbox("Numeric field", numeric, index=0)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.histogram(data, x=selected, marginal="box", template="simple_white"), width="stretch")
    with right:
        st.plotly_chart(px.box(data, y=selected, template="simple_white"), width="stretch")
    if len(numeric) > 1:
        st.subheader("Correlation matrix")
        st.plotly_chart(px.imshow(data[numeric].corr(), text_auto=True, color_continuous_scale="RdYlGn", aspect="auto"), width="stretch")


def _segmentation(result):
    segments = result["segments"]
    if segments.empty:
        st.info("No segment-like column was detected in this dataset.")
        return
    st.dataframe(segments, width="stretch")
    metric = "revenue" if "revenue" in segments else "records"
    st.plotly_chart(px.bar(segments, x="segment", y=metric, color="segment", template="simple_white"), width="stretch")


def _sql(result):
    validation = result["sql"]
    st.metric("Validation status", validation["status"])
    st.dataframe(pd.DataFrame([validation]), width="stretch")
    st.caption("The SQL check runs against an in-memory SQLite copy of the cleaned dataset.")


def _insights(result):
    for insight in result["insights"]:
        with st.container(border=True):
            st.subheader(insight["title"])
            st.write(insight["description"])
            st.caption(f"Severity: {insight['severity']}  |  Confidence: {insight['confidence']}")


def _reports(result):
    markdown = report_markdown(result, "DataLens project")
    st.download_button("Download Markdown report", markdown, "datalens_report.md", "text/markdown")
    st.code(markdown, language="markdown")


def _alerts(result):
    revenue = result["kpis"].get("revenue")
    threshold = st.number_input("Revenue alert threshold", min_value=0.0, value=float(revenue or 0), step=100.0)
    if revenue is not None and revenue < threshold:
        st.warning(f"Revenue threshold breached: {revenue:,.2f} is below {threshold:,.2f}.")
    else:
        st.success("No revenue threshold breach.")


if __name__ == "__main__":
    main()