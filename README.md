# Credly Ingestion Service

Serverless backend for ingesting badges and templates from Credly API.

## Setup

1.  **Install Dependencies**:
    This project uses `uv`.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv sync
    ```

2.  **Local Environment**:
    Start LocalStack using Podman:
    ```bash
    podman-compose up -d
    ```

3.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your credentials:
    ```bash
    cp .env.example .env
    ```
    *   `CREDLY_ORG_ID`: Your Credly Organization ID.
    *   `CREDLY_API_TOKEN`: Your Authorization Token (for DEV/Local).

## Running Locally

To run the ingestion locally (simulating a historical load of 50 badges):

```bash
uv run python scripts/run_lambda_local.py
```

This script will:
1.  Read credentials from `.env`.
2.  Update the LocalStack Secrets Manager with your token.
3.  Invoke the Lambda Handler locally.

## Verifying Data

To list files in the LocalStack S3 bucket and view the latest content:

```bash
./scripts/check_s3_data.sh
```

## Testing

Run unit tests:
```bash
uv run pytest tests/
```
