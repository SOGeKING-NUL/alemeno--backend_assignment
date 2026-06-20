# AI-Powered Transaction Processing Pipeline

This is a backend service built with FastAPI, PostgreSQL, Celery, and Redis to asynchronously process and categorize financial transactions using an LLM (Gemini 1.5 Flash).

## Tech Stack
- **FastAPI**: High-performance async web framework.
- **PostgreSQL**: Relational database for transactions and jobs.
- **Celery + Redis**: Background task queue and message broker.
- **Docker Compose**: Single-command container orchestration.
- **Pandas**: Efficient CSV parsing and vectorized data cleaning.
- **Google GenAI SDK**: Integration with Gemini 1.5 Flash.

## Setup Instructions

1. **Environment Variables**:
   Copy the example environment file and fill in your Gemini API key:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set `GEMINI_API_KEY=your_actual_key_here`.

2. **Run the Application**:
   Start the entire stack using Docker Compose:
   ```bash
   docker compose up --build
   ```

   The API will be available at `http://localhost:8000`.
   Interactive API documentation (Swagger UI) is at `http://localhost:8000/docs`.

## Example Usage (cURL)

**1. Upload a CSV file:**
```bash
curl -X 'POST' \
  'http://localhost:8000/jobs/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@transactions.csv'
```
*(Returns a `job_id` like `{"id": 1, "filename": "transactions.csv", ...}`)*

**2. Check Job Status:**
```bash
curl -X 'GET' \
  'http://localhost:8000/jobs/1/status' \
  -H 'accept: application/json'
```
*(Status will transition from `pending` -> `processing` -> `completed` or `failed`)*

**3. Fetch Processing Results:**
```bash
curl -X 'GET' \
  'http://localhost:8000/jobs/1/results' \
  -H 'accept: application/json'
```
*(Returns full structured JSON including cleaned transactions, anomalies, categories, and narrative summary)*

**4. List All Jobs:**
```bash
curl -X 'GET' \
  'http://localhost:8000/jobs?status=completed' \
  -H 'accept: application/json'
```
