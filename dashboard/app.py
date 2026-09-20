

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="InsightFlow AI",
    page_icon="📊",
    layout="wide"
)

st.title("InsightFlow AI")
st.caption("Data Quality and Analytics Dashboard")


def get_api_data(endpoint: str):
    """
    Calls a FastAPI endpoint and returns JSON data.

    Returning None means the request failed, so the dashboard
    can show a friendly message instead of crashing.
    """
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None


database_data = get_api_data("/database-health")

if not database_data:
    st.error(
        "Cannot connect to FastAPI. "
        "Start the backend first."
    )

    st.stop()

st.success(
    f"Backend connected to: "
    f"{database_data['database']}"
)


pipeline_runs = get_api_data("/pipeline-runs")

if pipeline_runs is None:
    st.error("Could not load pipeline history.")

    st.stop()


# Depending on your API response, the list may be returned directly
# or inside a key called `pipeline_runs`.
if isinstance(pipeline_runs, dict):
    pipeline_runs = pipeline_runs.get(
        "pipeline_runs",
        []
    )


if not pipeline_runs:
    st.info(
        "No pipeline runs found yet. "
        "Upload a CSV through FastAPI first."
    )

    st.stop()


runs_dataframe = pd.DataFrame(pipeline_runs)

total_uploads = len(runs_dataframe)

total_original_rows = int(
    runs_dataframe["original_rows"].sum()
)

total_ready_rows = int(
    runs_dataframe["ready_rows"].sum()
)

total_quarantined_rows = int(
    runs_dataframe["quarantined_rows"].sum()
)


st.subheader("Pipeline Overview")

column_1, column_2, column_3, column_4 = st.columns(4)

column_1.metric(
    "Total Uploads",
    total_uploads
)

column_2.metric(
    "Original Rows",
    total_original_rows
)

column_3.metric(
    "Ready for Analytics",
    total_ready_rows
)

column_4.metric(
    "Quarantined Rows",
    total_quarantined_rows
)


st.subheader("Pipeline Run History")

history_columns = [
    "id",
    "filename",
    "quality_status",
    "original_rows",
    "ready_rows",
    "quarantined_rows",
    "created_at"
]

available_columns = [
    column
    for column in history_columns
    if column in runs_dataframe.columns
]

st.dataframe(
    runs_dataframe[available_columns],
    use_container_width=True,
    hide_index=True
)

st.subheader("Data Quality by Upload")

quality_counts = (
    runs_dataframe["quality_status"]
    .value_counts()
    .reset_index()
)

quality_counts.columns = [
    "quality_status",
    "upload_count"
]

quality_chart = px.pie(
    quality_counts,
    names="quality_status",
    values="upload_count",
    color="quality_status",
    color_discrete_map={
        "ready_for_analytics": "#22c55e",
        "needs_review": "#ef4444"
    },
    title="Upload Quality Status"
)

st.plotly_chart(
    quality_chart,
    use_container_width=True
)

st.divider()

st.subheader("Stored Datasets")

datasets = get_api_data("/datasets")

if datasets is None:
    st.error("Could not load stored datasets.")

elif not datasets:
    st.info("No stored datasets found.")

else:
    datasets_dataframe = pd.DataFrame(datasets)

    st.dataframe(
        datasets_dataframe[
            [
                "id",
                "filename",
                "table_name",
                "rows_count",
                "columns_count",
                "created_at"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    selected_dataset_id = st.selectbox(
        "Select a dataset",
        options=datasets_dataframe["id"].tolist(),
        format_func=lambda dataset_id: (
            datasets_dataframe.loc[
                datasets_dataframe["id"] == dataset_id,
                "filename"
            ].iloc[0]
        )
    )

    selected_dataset = datasets_dataframe[
        datasets_dataframe["id"] == selected_dataset_id
    ].iloc[0]

    left_column, middle_column, right_column = st.columns(3)

    left_column.metric(
        "Rows",
        selected_dataset["rows_count"]
    )

    middle_column.metric(
        "Columns",
        selected_dataset["columns_count"]
    )

    right_column.metric(
        "Database Table",
        selected_dataset["table_name"]
    )



    st.subheader("Dataset Preview")

preview_data = get_api_data(
    f"/datasets/{selected_dataset_id}/preview"
)

if preview_data is None:
    st.error("Could not load dataset preview.")

elif not preview_data["rows"]:
    st.warning("This dataset does not contain any rows.")

else:
    preview_dataframe = pd.DataFrame(
        preview_data["rows"]
    )

    st.dataframe(
        preview_dataframe,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing up to 20 rows from "
        f"`{preview_data['table_name']}`."
    )

    st.divider()

st.subheader("Task Analytics")

if preview_data and preview_data["rows"]:
    analytics_dataframe = pd.DataFrame(
        preview_data["rows"]
    )

    chart_left, chart_right = st.columns(2)

    if "Status" in analytics_dataframe.columns:
        status_counts = (
            analytics_dataframe["Status"]
            .value_counts()
            .reset_index()
        )

        status_counts.columns = [
            "Status",
            "Task Count"
        ]

        status_chart = px.bar(
            status_counts,
            x="Status",
            y="Task Count",
            color="Status",
            title="Tasks by Status"
        )

        chart_left.plotly_chart(
            status_chart,
            use_container_width=True
        )

    if "Priority" in analytics_dataframe.columns:
        priority_counts = (
            analytics_dataframe["Priority"]
            .value_counts()
            .reset_index()
        )

        priority_counts.columns = [
            "Priority",
            "Task Count"
        ]

        priority_chart = px.pie(
            priority_counts,
            names="Priority",
            values="Task Count",
            title="Tasks by Priority"
        )

        chart_right.plotly_chart(
            priority_chart,
            use_container_width=True
        )

    if "Layer" in analytics_dataframe.columns:
        layer_counts = (
            analytics_dataframe["Layer"]
            .value_counts()
            .reset_index()
        )

        layer_counts.columns = [
            "Layer",
            "Task Count"
        ]

        layer_chart = px.bar(
            layer_counts,
            x="Layer",
            y="Task Count",
            color="Layer",
            title="Tasks by Project Layer"
        )

        st.plotly_chart(
            layer_chart,
            use_container_width=True
        )

    if "Estimated_Hours" in analytics_dataframe.columns:
        estimated_hours = pd.to_numeric(
            analytics_dataframe["Estimated_Hours"],
            errors="coerce"
        ).sum()

        st.metric(
            "Total Estimated Hours",
            f"{estimated_hours:.1f}"
        )

else:
    st.info(
        "Choose a dataset with rows to view task analytics."
    )