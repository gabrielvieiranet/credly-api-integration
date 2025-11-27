# Scripts Directory

This directory contains utility scripts for managing the Credly Ingestion project environment and running tests.

## Core Workflows

### 1. Reset Environment
Use this script to clean all resources (S3, DynamoDB, Secrets Manager), recreate infrastructure via Terraform, and populate the API token.

```bash
./scripts/reset_environment.sh
```

**What it does:**
- Deletes existing S3 bucket, DynamoDB table, and Secrets Manager secret.
- Re-initializes and applies Terraform configuration (LocalStack).
- Updates the `my-app/credentials` secret in LocalStack with your local `CREDLY_API_TOKEN`.

### 2. Run Daily Test Simulation
Use this script to simulate the daily Step Functions execution flow and validate the results.

```bash
./scripts/run_daily_test.sh
```

**What it does:**
- Runs `simulate_step_function.py` for both Badges and Templates in `daily` mode.
- Simulates the Step Functions pagination loop (Process -> Check -> Continue).
- Generates CSV reports from the data written to S3 to validate correctness.

### 3. Run Full Historical Test (Badges Only)
Use this script to simulate a larger historical load for badges (4 pages), excluding templates.

```bash
./scripts/run_full_test.sh
```

**What it does:**
- Runs `simulate_step_function.py` with `--load-type badges`, `--mode historical`, and `--max-pages 4`.
- Simulates fetching 4 pages of badges (approx. 4000 records).
- Generates CSV reports.

### 4. Run Incremental Load Test (Badges Only)
Use this script to verify the watermark logic for badges.

```bash
./scripts/run_incremental_test.sh
```

**What it does:**
- Resets the environment.
- Runs a first daily load (simulating "yesterday").
- Verifies that a watermark was created in DynamoDB.
- Runs a second daily load (simulating "today").
- Verifies that the watermark was updated.

## Helper Scripts

- **`setup_infra.sh`**: The underlying script used by `reset_environment.sh` to manage Terraform and AWS resources.
- **`update_local_token.sh`**: Updates the Credly API token in LocalStack Secrets Manager.
- **`simulate_step_function.py`**: Python script that implements the Step Functions logic locally for testing.
- **`generate_csv_reports.py`**: Reads Parquet files from S3 and generates CSV reports for validation.
- **`run_lambda_local.py`**: Helper module to invoke the Lambda handler locally.
