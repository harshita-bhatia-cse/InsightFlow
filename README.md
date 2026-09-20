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
- Shows total uploads
- Shows original, ready, and quarantined row totals
- Displays pipeline run history
- Displays upload quality status as a chart
- Lists stored datasets
- Allows selecting a dataset
- Shows up to 20 preview rows
- Shows task counts by status
- Shows task counts by priority
- Shows task counts by layer
- Shows total estimated hours for the displayed preview

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

## Current limitations

The following functionality is not complete yet:

- Direct CSV upload from the Streamlit dashboard
- Full profile-report dashboard
- Advanced column statistics
- Analytics over the complete dataset rather than the 20-row preview
- Time-based trend analysis
- Business KPI engine
- Recommendations and AI-generated insights
- User authentication and authorization
- Automated test suite
- Database migration system
- Production deployment configuration
- Reproducible dependency manifest

## Next development milestones

Recommended next steps:

1. Add a profile retrieval API and profile section to the dashboard.
2. Calculate analytics from the full stored dataset, not only the preview.
3. Add `st.file_uploader()` to the dashboard.
4. Add business KPIs and trend analysis.
5. Add insight and recommendation generation.
6. Add automated tests for validation, cleaning, profiling, and API routes.
7. Add dependency management and database migrations.
8. Add authentication before exposing the application beyond local use.

## Project summary

InsightFlow AI currently provides the foundation of a data-governed analytics
platform. It converts uploaded task CSV files into validated, cleaned,
profiled, traceable, and queryable datasets, while preserving unsafe records for
manual review. A Streamlit dashboard provides an initial operational view of
pipeline quality and task-level analytics.
