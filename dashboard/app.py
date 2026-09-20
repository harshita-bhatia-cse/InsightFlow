import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="InsightFlow AI", page_icon="📊", layout="wide")

@st.cache_data(ttl=30)
def api(endpoint: str):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        st.error(f"API request failed: {error}")
        return None

def chart(items, title, x="name", y="count"):
    if items:
        st.plotly_chart(px.bar(pd.DataFrame(items), x=x, y=y, color=x, title=title), use_container_width=True)
    else:
        st.info("No data is available for this chart.")

st.title("InsightFlow AI")
st.caption("Executive Analytics Dashboard")
if not api("/database-health"):
    st.stop()
datasets = api("/datasets")
if not datasets:
    st.info("No stored datasets found. Upload a CSV through the pipeline first.")
    st.stop()

catalog = pd.DataFrame(datasets)
selected_id = st.sidebar.selectbox(
    "Analyze dataset", catalog["id"].tolist(),
    format_func=lambda value: f"{catalog.loc[catalog['id'] == value, 'filename'].iloc[0]} (ID {value})",
)
page = st.sidebar.radio("Analytics page", ["Executive Dashboard", "Dataset Profile", "Statistics", "KPIs", "Trends", "Insights", "Recommendations"])

if page == "Executive Dashboard":
    kpis, insights = api(f"/analytics/kpis/{selected_id}"), api(f"/analytics/insights/{selected_id}")
    if kpis:
        st.subheader("Executive Summary")
        a, b, c, d = st.columns(4)
        a.metric("Total Tasks", kpis["total_tasks"]); b.metric("Completion Rate", f"{kpis['completion_rate']:.1f}%")
        c.metric("Pending Tasks", kpis["pending_tasks"]); d.metric("Estimated Hours", f"{kpis['total_estimated_hours']:.1f}")
        left, right = st.columns(2)
        with left: chart(kpis["layer_workload_distribution"], "Workload by Layer", y="estimated_hours")
        with right: chart(kpis["component_distribution"], "Tasks by Component")
    if insights:
        st.subheader("Key Insights")
        for item in insights["insights"]:
            getattr(st, "error" if item["severity"] == "high" else "warning")(f"{item['title']}: {item['message']}")

elif page == "Dataset Profile":
    data = api(f"/profiles/{selected_id}")
    if data:
        st.subheader(f"Dataset Profile: {data['filename']}")
        a, b = st.columns(2); a.metric("Rows", data["summary"]["rows"]); b.metric("Columns", data["summary"]["columns"])
        st.dataframe(pd.DataFrame(data["columns"]), use_container_width=True, hide_index=True)
        chart([{"column": key, "missing_count": value} for key, value in data["missing_value_analysis"].items()], "Missing Values by Column", x="column", y="missing_count")

elif page == "Statistics":
    data = api(f"/analytics/statistics/{selected_id}")
    if data:
        stats = pd.DataFrame(data["numeric_statistics"]).T.reset_index(names="column")
        if stats.empty: st.info("The selected dataset has no numeric columns.")
        else:
            st.dataframe(stats, use_container_width=True, hide_index=True)
            correlation = pd.DataFrame(data["correlation_matrix"])
            if not correlation.empty:
                figure = go.Figure(data=go.Heatmap(z=correlation.values, x=correlation.columns, y=correlation.index, colorscale="Blues", zmin=-1, zmax=1))
                figure.update_layout(title="Correlation Matrix"); st.plotly_chart(figure, use_container_width=True)
            st.subheader("Outlier Summary")
            st.dataframe(pd.DataFrame(data["outlier_summary"]).T.reset_index(names="column"), use_container_width=True, hide_index=True)

elif page == "KPIs":
    data = api(f"/analytics/kpis/{selected_id}")
    if data:
        a, b, c, d = st.columns(4)
        a.metric("Total Tasks", data["total_tasks"]); b.metric("Completed", data["completed_tasks"], f"{data['completion_rate']:.1f}%")
        c.metric("Pending", data["pending_tasks"], f"{data['pending_rate']:.1f}%"); d.metric("High-Priority Pending", data["high_priority_pending_tasks"])
        chart(data["layer_workload_distribution"], "Layer Workload Distribution", y="estimated_hours")
        chart(data["component_distribution"], "Component Distribution")

elif page == "Trends":
    data = api(f"/analytics/trends/{selected_id}")
    if data:
        left, right = st.columns(2)
        with left: chart(data["status_trends"], "Status Trend")
        with right: chart(data["priority_trends"], "Priority Trend")
        chart(data["layer_trends"], "Layer Trend")
        if data["time_trends"]:
            grain = st.selectbox("Time grain", list(data["time_trends"]))
            values = pd.DataFrame(data["time_trends"][grain])
            st.plotly_chart(px.line(values, x="period", y="count", markers=True, title=f"{grain.title()} Trend"), use_container_width=True)
        else: st.info("No date/time column was found for time-based trend analysis.")

elif page == "Insights":
    data = api(f"/analytics/insights/{selected_id}")
    if data:
        for item in data["insights"]:
            getattr(st, "error" if item["severity"] == "high" else "warning")(f"{item['title']}: {item['message']}")
        if not data["insights"]: st.info("No rule-based insights were generated.")

elif page == "Recommendations":
    data = api(f"/analytics/recommendations/{selected_id}")
    if data:
        for item in data["recommendations"]:
            st.markdown(f"**{item['priority'].title()} priority — {item['recommendation']}**  \n{item['rationale']}")
        if not data["recommendations"]: st.info("No recommendations were generated.")
