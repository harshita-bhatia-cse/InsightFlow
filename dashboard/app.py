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


def upload_csv(uploaded_file):
    try:
        response = requests.post(
            f"{API_URL}/upload",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "text/csv",
                )
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        st.error(f"Upload failed: {error}")
        return None


def chart(items, title, x="name", y="count"):
    if items:
        st.plotly_chart(px.bar(pd.DataFrame(items), x=x, y=y, color=x, title=title), use_container_width=True)
    else:
        st.info("No data is available for this chart.")


def donut_chart(items, title):
    if not items:
        st.info("No data is available for this chart.")
        return

    values = pd.DataFrame(items)
    figure = px.pie(
        values,
        names="name",
        values="count",
        hole=0.55,
        title=title,
    )
    figure.update_layout(showlegend=True, margin=dict(t=55, l=10, r=10, b=10))
    st.plotly_chart(figure, use_container_width=True)


def quality_gauge(score):
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score),
            number={"suffix": "/100"},
            title={"text": "Data Quality"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2563eb"},
                "steps": [
                    {"range": [0, 60], "color": "#fee2e2"},
                    {"range": [60, 80], "color": "#fef3c7"},
                    {"range": [80, 100], "color": "#dcfce7"},
                ],
            },
        )
    )
    figure.update_layout(height=280, margin=dict(t=55, l=25, r=25, b=15))
    st.plotly_chart(figure, use_container_width=True)


def render_action(item, kind):
    level = item.get("severity" if kind == "insight" else "priority", "low").lower()
    message = (
        f"**{item.get('title', 'Insight')}**  \n{item.get('message', '')}"
        if kind == "insight"
        else (
            f"**{item.get('recommendation', 'Recommendation')}**  \n"
            f"{item.get('rationale', '')}"
        )
    )

    if level == "high":
        st.error(message)
    elif level == "medium":
        st.warning(message)
    else:
        st.info(message)


st.title("InsightFlow AI")
st.caption("Executive Analytics Dashboard")
if not api("/database-health"):
    st.stop()

st.sidebar.subheader("Data pipeline")

uploaded_file = st.sidebar.file_uploader(
    "Upload task CSV",
    type=["csv"],
)

if st.sidebar.button(
    "Process CSV",
    disabled=uploaded_file is None,
):
    upload_result = upload_csv(uploaded_file)

    if upload_result is not None:
        st.sidebar.success(
            f"Processed {upload_result['filename']} "
            f"({upload_result['quality_status']})."
        )
        st.cache_data.clear()
        st.rerun()

if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

datasets = api("/datasets")
if not datasets:
    st.info("No stored datasets found. Upload a CSV through the pipeline first.")
    st.stop()

catalog = pd.DataFrame(datasets)
selected_id = st.sidebar.selectbox(
    "Analyze dataset", catalog["id"].tolist(),
    format_func=lambda value: f"{catalog.loc[catalog['id'] == value, 'filename'].iloc[0]} (ID {value})",
)
page = st.sidebar.radio(
    "Analytics page",
    [
        "Executive Dashboard",
        "Dataset Profile",
        "Data Quality",
        "Statistics",
        "KPIs",
        "Trends",
        "Insights",
        "Recommendations",
    ],
)
if page == "Executive Dashboard":
    dataset = catalog.loc[
        catalog["id"] == selected_id
    ].iloc[0]

    kpis = api(
        f"/analytics/kpis/{selected_id}"
    )

    quality = api(
        f"/analytics/quality/{selected_id}"
    )

    trends = api(
        f"/analytics/trends/{selected_id}"
    )

    insights = api(
        f"/analytics/insights/{selected_id}"
    )

    recommendations = api(
        f"/analytics/recommendations/{selected_id}"
    )

    st.subheader("Executive Overview")

    st.caption(
        f"Dataset: {dataset['filename']}  |  "
        f"Loaded: {dataset.get('rows_count', 'n/a'):,} rows  |  "
        f"Dataset ID: {selected_id}"
    )

    if kpis:
        metric_columns = st.columns(5)

        metric_columns[0].metric(
            "Total Tasks",
            f"{kpis['total_tasks']:,}",
        )

        metric_columns[1].metric(
            "Completion Rate",
            f"{kpis['completion_rate']:.1f}%",
            f"{kpis['completed_tasks']:,} completed",
        )

        metric_columns[2].metric(
            "Pending Tasks",
            f"{kpis['pending_tasks']:,}",
            f"{kpis['pending_rate']:.1f}% of total",
            delta_color="inverse",
        )

        metric_columns[3].metric(
            "High-Priority Pending",
            f"{kpis['high_priority_pending_tasks']:,}",
            delta_color="inverse",
        )

        metric_columns[4].metric(
            "Estimated Hours",
            f"{kpis['total_estimated_hours']:,.1f}",
        )

        left, right = st.columns(
            [1, 1.5]
        )

        with left:
            completion = pd.DataFrame(
                [
                    {
                        "name": "Completed",
                        "count": kpis[
                            "completed_tasks"
                        ],
                    },
                    {
                        "name": "Pending",
                        "count": kpis[
                            "pending_tasks"
                        ],
                    },
                ]
            )

            donut_chart(
                completion.to_dict(
                    "records"
                ),
                "Delivery Status",
            )

        with right:
            chart(
                kpis[
                    "layer_workload_distribution"
                ],
                "Estimated Workload by Layer",
                y="estimated_hours",
            )

    st.divider()

    quality_column, status_column = st.columns(
        [1, 1.5]
    )

    with quality_column:
        if quality:
            quality_gauge(
                quality.get(
                    "quality_score",
                    0,
                )
            )

            quality_metrics = quality.get(
                "metrics",
                {},
            )

            st.metric(
                "Quality Grade",
                quality.get(
                    "grade",
                    "N/A",
                ),
                (
                    f"Quarantine: "
                    f"{quality_metrics.get(
                        'quarantine_rate',
                        0,
                    ):.1f}%"
                ),
            )

    with status_column:
        if trends:
            donut_chart(
                trends.get(
                    "status_trends",
                    [],
                ),
                "Task Status Mix",
            )

    action_column, recommendation_column = st.columns(
        2
    )

    with action_column:
        st.subheader("Key Insights")

        insight_items = (
            insights.get(
                "insights",
                [],
            )
            if insights
            else []
        )

        if insight_items:
            for item in insight_items[:5]:
                render_action(
                    item,
                    "insight",
                )
        else:
            st.success(
                "No immediate risks were detected."
            )

    with recommendation_column:
        st.subheader("Recommended Actions")

        recommendation_items = (
            recommendations.get(
                "recommendations",
                [],
            )
            if recommendations
            else []
        )

        if recommendation_items:
            for item in recommendation_items[:5]:
                render_action(
                    item,
                    "recommendation",
                )
        else:
            st.success(
                "No recommendations are pending."
            )
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

elif page == "Data Quality":
    data = api(
        f"/analytics/quality/{selected_id}"
    )

    if data:
        st.subheader("Data Quality Score")

        score = data.get(
            "quality_score",
            0,
        )

        grade = data.get(
            "grade",
            "N/A",
        )

        metrics = data.get(
            "metrics",
            {},
        )

        summary = data.get(
            "summary",
            {},
        )

        score_column, grade_column = st.columns(2)

        score_column.metric(
            "Overall Quality Score",
            f"{score:.1f}/100",
        )

        grade_column.metric(
            "Quality Grade",
            grade,
        )

        st.subheader("Quality Metrics")

        metric_1, metric_2, metric_3, metric_4 = st.columns(4)

        metric_1.metric(
            "Completeness",
            f"{metrics.get('completeness_score', 0):.1f}%",
        )

        metric_2.metric(
            "Uniqueness",
            f"{metrics.get('uniqueness_score', 0):.1f}%",
        )

        metric_3.metric(
            "Validity",
            f"{metrics.get('validity_score', 0):.1f}%",
        )

        metric_4.metric(
            "Readiness",
            f"{metrics.get('readiness_score', 0):.1f}%",
        )

        st.subheader("Dataset Quality Summary")

        summary_dataframe = pd.DataFrame(
            [
                {
                    "Metric": "Original Rows",
                    "Value": summary.get(
                        "original_rows",
                        0,
                    ),
                },
                {
                    "Metric": "Ready Rows",
                    "Value": summary.get(
                        "ready_rows",
                        0,
                    ),
                },
                {
                    "Metric": "Quarantined Rows",
                    "Value": summary.get(
                        "quarantined_rows",
                        0,
                    ),
                },
                {
                    "Metric": "Missing Values",
                    "Value": summary.get(
                        "missing_value_count",
                        0,
                    ),
                },
                {
                    "Metric": "Duplicate Rows",
                    "Value": summary.get(
                        "duplicate_row_count",
                        0,
                    ),
                },
                {
                    "Metric": "Duplicate Task IDs",
                    "Value": summary.get(
                        "duplicate_task_id_count",
                        0,
                    ),
                },
            ]
        )

        st.dataframe(
            summary_dataframe,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Quality Issues")

        issues = data.get(
            "issues",
            [],
        )

        if not issues:
            st.success(
                "No quality issues were detected."
            )
        else:
            issues_dataframe = pd.DataFrame(
                issues
            )

            st.dataframe(
                issues_dataframe,
                use_container_width=True,
                hide_index=True,
            )

        st.metric(
            "Quarantine Rate",
            f"{metrics.get('quarantine_rate', 0):.1f}%",
        )

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
