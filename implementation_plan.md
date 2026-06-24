# Current Implementation Plan & Architecture

This document encapsulates the current implementation of the AI-Powered Transaction Processing Pipeline, detailing the architecture, how the different components are set up, and why these technical choices act as solutions to the requirements.

## 1. System Architecture & Setup

The backend is built as a highly modular FastAPI application, adhering to **Domain-Driven Design (DDD)** principles. This architectural choice prevents the codebase from becoming an unmaintainable monolith, ensuring clear separation of concerns.

The application is containerized using **Docker** and **Docker Compose**, orchestrating the FastAPI server, Celery Worker, PostgreSQL database, and Redis broker with a single `docker compose up` command.

### Codebase Structure

- `app/api/routes/`: Contains the API endpoints (`/jobs/upload`, `/jobs/{job_id}/status`, etc.). It acts strictly as the entry point for HTTP requests.
- `app/core/`: The "Engine Room". Contains global configurations (`config.py` using Pydantic for strict environment variable validation) and database session management.
- `app/models/`: Defines the SQLAlchemy ORM models (`Job`, `Transaction`, `JobSummary`), translating Python classes directly into PostgreSQL tables.
- `app/schemas/`: Houses Pydantic schemas. These validate incoming and outgoing JSON payloads, ensuring strict typing and security.
- `app/services/`: Where the core business logic resides (`data_cleaner.py`, `anomaly_detector.py`, `llm_service.py`).
- `app/worker/`: Contains the Celery application and background tasks (`tasks.py`). This allows resource-intensive operations (like parsing CSVs and calling LLMs) to run asynchronously without blocking the main API thread.

## 2. Request Lifecycle & Data Flow

Here is the exact path a single request takes through the system:

### A. Ingestion (FastAPI)
1. The user calls `POST /jobs/upload` with a CSV file.
2. The endpoint validates the file extension and saves the file locally in the `uploads/` directory.
3. A `Job` record is created in PostgreSQL with `status="pending"`.
4. A Celery task (`process_transaction_file.delay`) is dispatched to the Redis broker, containing the `job_id` and `file_path`.
5. The API immediately returns the `job_id` to the user, providing a fast, non-blocking response.

### B. Background Processing (Celery Worker)
The Celery worker dequeues the task and executes the following pipeline:

1. **Data Loading**: Pandas (`pd.read_csv`) loads the CSV into memory.
2. **Data Cleaning (`clean_data`)**: Normalizes dates to ISO 8601, strips currency symbols, standardizes casing, and removes exact duplicates.
3. **Anomaly Detection (`detect_anomalies`)**: Flags transactions using statistical logic (amount > 3x median) and business logic (USD currency for domestic merchants).
4. **LLM Classification (`llm_service.py`)**: 
    - **How**: Filters for transactions with the category `Uncategorised`.
    - **Why**: Instead of making one API call per row, the system batches these rows into a single list and sends them to the LLM (e.g., OpenRouter). This saves significant time and API costs.
    - **Retry Logic**: Uses the `tenacity` library to automatically retry failed LLM calls up to 3 times with exponential backoff, preventing transient API errors from crashing the job.
5. **Database Persistence**: Iterates through the cleaned dataframe, instantiates SQLAlchemy `Transaction` objects, and bulk inserts them into PostgreSQL.
6. **LLM Narrative Summary**: Generates a high-level narrative summary using total spends and anomaly counts, which is persisted into the `JobSummary` table.
7. **Completion**: Updates the `Job` status to "completed".

## 3. The "Why": Technical Reasoning & Solutions

- **FastAPI + Celery/Redis**: Parsing files and waiting for LLM APIs can take seconds or minutes. Offloading this to a Celery worker ensures the FastAPI event loop remains unblocked, allowing it to serve hundreds of concurrent status queries (`GET /jobs/{job_id}/status`) effortlessly.
- **SQLAlchemy + Pydantic**: Provides a strong contract between the database and the client. Pydantic schemas automatically serialize complex objects (like datetime and nested JSON summaries) into clean JSON responses.
- **Pandas**: Used for data cleaning because of its highly optimized, vectorized operations. Operations that take seconds in raw Python loops are executed in milliseconds via Pandas C-extensions.

---

> [!WARNING]  
> ## 4. Bottlenecks & Future Scaling Plans
> 
> If application traffic scales by 100x, the current codebase will critically fail in three specific areas. Below are the planned architectural changes for enterprise production.

### A. Memory Exhaustion
**The Breaking Point**: The worker uses `pd.read_csv` to load the entire CSV file into RAM at once. 100 concurrent 2GB uploads will cause an Out-Of-Memory (OOM) crash. Furthermore, `db.add_all()` attempts to commit all rows in one giant memory transaction.
**The Solution (Chunked Processing)**: Replace the monolithic Pandas read with chunked processing (e.g., `pd.read_csv(chunksize=5000)`). Process and save rows to the database in strict chunks. This slightly increases database I/O overhead but guarantees the worker will never run out of RAM.

### B. Stateful Local Storage
**The Breaking Point**: FastAPI saves uploads to a local disk (`/uploads`). If scaled horizontally behind a Load Balancer, a file uploaded to Server A cannot be found by a worker running on Server B.
**The Solution (Cloud Object Storage)**: The frontend should upload the file directly to an AWS S3 Bucket using a Pre-Signed URL. FastAPI will only pass the `s3://...` URI to Celery. This adds slight network latency but makes the FastAPI servers 100% stateless and infinitely scalable.

### C. LLM Token Limits
**The Breaking Point**: Batching all uncategorized rows into a single prompt will exceed the LLM’s maximum context window, resulting in a `400 Token Limit Exceeded` error.
**The Solution (Sub-Tasking)**: Break uncategorized rows into chunks (e.g., 50 rows per prompt) and spawn a Celery "Sub-Task" (using Celery Chords or Groups) for each chunk. This allows for massive parallel processing and prevents token overflow.
