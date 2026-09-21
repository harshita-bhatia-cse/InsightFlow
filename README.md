# InsightFlow AI

InsightFlow AI is a data-quality and analytics platform for project-task CSV files.
The current version implements the ingestion foundation and an initial analytics
dashboard:

```text
CSV upload
    ↓
FastAPI ingestion
    ↓
Validation and business rules
    ↓
Safe cleaning
    ↓
Quarantine unsafe records
    ↓
Dataset profiling
    ↓
PostgreSQL storage
    ↓
Streamlit dashboard and task analytics
```

## Current status

The project currently includes:

- FastAPI backend running on port `8000`
- CSV upload and file-size validation
- Pandas-based ingestion and cleaning
- A task-data contract with required fields
- Duplicate and missing-value checks
- Quarantine handling for unsafe rows
- Processed and quarantined CSV output files
- UUID-based pipeline-run traceability
- PostgreSQL and SQLAlchemy integration
- Pipeline-run and dataset metadata storage
- Dynamic PostgreSQL tables for cleaned datasets
- Dataset profiling and profile persistence
- Streamlit dashboard
- Pipeline KPIs and run history
- Dataset selection and data preview
- Basic task analytics using Plotly charts

## Project structure

```text
InsightFlow/
├── app/
│   ├── main.py                         # FastAPI application and pipeline routes
│   ├── database/
│   │   ├── connection.py               # SQLAlchemy engine and sessions
│   │   ├── models.py                   # PipelineRun, Dataset, DatasetProfile
│   │   └── profile_repository.py       # Profile persistence
│   └── profiling/
│       └── profiler.py                 # Dataset profiling logic
├── dashboard/
│   └── app.py                          # Streamlit dashboard
├── data/
│   ├── processed/                      # Cleaned datasets
│   └── quarantine/                     # Unsafe records for review
├── .env                                # Local database configuration
├── file.txt                            # Development architecture notes
└── README.md
```

The `.venv` directory contains the local Python environment and should not be
committed or included in project documentation.

## Data contract

The current task-data contract expects these columns:

```text
Task_ID
Layer
Component
Status
Priority
Estimated_Hours
```

The required fields are:

```text
Task_ID
Status
```

The backend validates:

- Missing expected columns
- Unexpected columns
- Missing values
- Missing required fields
- Exact duplicate rows
- Duplicate `Task_ID` values

## Data cleaning and quarantine rules

The pipeline applies conservative cleaning rules:

- Column names and string values are trimmed.
- Empty strings are treated as missing values.
- Exact duplicate rows are removed.
- Missing `Layer`, `Component`, and `Priority` values can be filled with
  `Unknown`.
- Missing `Estimated_Hours` values are filled with the available median.
- Missing `Task_ID` and `Status` values are never invented.
- Rows with missing required fields are quarantined.
- Rows with duplicate task IDs are quarantined.

Every upload produces:

```text
data/processed/{run_id}_ready.csv
data/quarantine/{run_id}_quarantine.csv
```

The `run_id` connects the files, API response, and database pipeline record.

## Dataset profiling

The profiling engine in `app/profiling/profiler.py` currently reports:

- Number of rows
- Number of columns
- Column names
- Numeric columns
- Categorical columns
- Datetime columns
- Missing-value counts by column

Profiles are saved in the `dataset_profiles` PostgreSQL table and are also
included in the upload response.

## Database models

The SQLAlchemy models are defined in `app/database/models.py`.

### `pipeline_runs`

Stores:

- Run ID
- Original filename
- Quality status
- Original row count
- Ready row count
- Quarantined row count
- Validation report
- Creation timestamp

### `datasets`

Stores:

- Dataset ID
- Original filename
- PostgreSQL table name
- Row count
- Column count
- Creation timestamp

### `dataset_profiles`

Stores:

- Profile ID
- Dataset name
- Profile data as JSON
- Creation timestamp

## Requirements

The project uses Python and expects these main packages:

- FastAPI
- Uvicorn
- Pandas
- SQLAlchemy
- Psycopg
- Python-dotenv
- Streamlit
- Plotly
- Requests

The project should eventually include a `requirements.txt` or
`pyproject.toml` file so the environment can be reproduced easily.

## Configuration

Create or update `.env` in the project root:

```env
DATABASE_URL=postgresql+psycopg://<username>:<password>@localhost:5432/insightflow_ai_db
```

Make sure:

- PostgreSQL is installed and running.
- The `insightflow_ai_db` database exists.
- The configured user has permission to create tables.

Do not commit real passwords or credentials to source control.

## Running the backend

Open PowerShell in the project directory:

```powershell
cd "C:\Users\Harshita Bhatia\Desktop\InsightFlow"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

Useful browser URLs:

- API health: `http://127.0.0.1:8000/health`
- Database health: `http://127.0.0.1:8000/database-health`
- Swagger documentation: `http://127.0.0.1:8000/docs`

## Running the dashboard

Keep the backend terminal running. Open a second PowerShell terminal:

```powershell
cd "C:\Users\Harshita Bhatia\Desktop\InsightFlow"
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

The dashboard normally opens at:

```text
http://localhost:8501
```

The dashboard currently:

- Checks backend and database connectivity
- Supports CSV upload and processing
- Lists stored datasets
- Allows selecting a dataset
- Provides an executive dashboard with delivery KPIs
- Visualizes completion status, workload by layer, and task status mix
- Displays data-quality score, grade, and quarantine rate
- Presents rule-based insights and prioritized recommendations
- Provides profile, quality, statistics, KPI, trend, insight, and recommendation pages

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Welcome response |
| `GET` | `/health` | Backend health check |
| `POST` | `/upload` | Upload and process a CSV |
| `GET` | `/downloads/{run_id}/{dataset_type}` | Download ready or quarantined CSV |
| `GET` | `/database-health` | Check PostgreSQL connectivity |
| `GET` | `/pipeline-runs` | List pipeline run history |
| `GET` | `/datasets` | List stored datasets |
| `GET` | `/datasets/{dataset_id}/preview` | Preview up to 20 stored rows |
| `GET` | `/profiles/{dataset_id}` | Return the dataset profile |
| `GET` | `/analytics/quality/{dataset_id}` | Calculate the data-quality score |
| `GET` | `/analytics/statistics/{dataset_id}` | Return numeric statistics and outliers |
| `GET` | `/analytics/kpis/{dataset_id}` | Return task and workload KPIs |
| `GET` | `/analytics/trends/{dataset_id}` | Return categorical and time trends |
| `GET` | `/analytics/insights/{dataset_id}` | Return rule-based insights |
| `GET` | `/analytics/recommendations/{dataset_id}` | Return prioritized recommendations |

## Upload workflow

The upload endpoint performs this sequence:

1. Check that a filename was provided.
2. Accept only `.csv` files.
3. Reject empty files.
4. Reject files larger than 5 MB.
5. Read the file into a Pandas DataFrame.
6. Normalize column names and text values.
7. Validate the original data.
8. Clean safe fields.
9. Quarantine unsafe records.
10. Profile the ready dataset.
11. Save ready and quarantined CSV files.
12. Save the ready dataset as a PostgreSQL table.
13. Save pipeline, dataset, and profile metadata.
14. Return summaries, previews, reports, and download links.

## Running tests

Run the complete automated test suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v


Save the file.

## 4. Start and verify FastAPI

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

## Current limitations

The following functionality is not complete yet:

- User authentication and authorization
- Automated test suite
- Database migration system
- Production deployment configuration
- Historical trend tracking across multiple dataset versions
- LLM-generated insights and recommendations

## Next development milestones

Recommended next steps:

1. Add automated unit and API tests.
2. Add database migrations and stronger dataset-to-pipeline relationships.
3. Add historical trend tracking across dataset versions.
4. Add authentication before exposing the application beyond local use.
5. Evaluate LLM-assisted insights and recommendations after rule-based behavior is covered by tests.

## Project summary

InsightFlow AI currently provides the foundation of a data-governed analytics
platform. It converts uploaded task CSV files into validated, cleaned,
profiled, traceable, and queryable datasets, while preserving unsafe records for
manual review. A Streamlit dashboard provides an initial operational view of
pipeline quality and task-level analytics.


COMMANDS
 python -m streamlit run dashboard/app.py
 python -m uvicorn app.main:app --reload