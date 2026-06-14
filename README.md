# EHR-Sync-Pipeline

A production-grade streaming data pipeline for Electronic Health Records (EHR). Synthetic patient, lab result, and medication data is generated in real time, streamed through Apache Kafka, validated and transformed, then persisted to PostgreSQL. A GraphQL API serves the stored data for downstream consumers.

## Architecture

```
Producers (Faker, 2s interval)
  ├── patient_data.py       → ehr.patient.events
  ├── lab_results_data.py   → ehr.labresults.events
  └── medications_data.py   → ehr.medications.events
                │
          Apache Kafka
          (consumer groups, manual offset commit)
                │
  ├── ehr-pipeline-patients
  ├── ehr-pipeline-labs
  ├── ehr-pipeline-meds
  └── ehr.dlq  (dead-letter queue)
                │
  Consumer ─► Pydantic Validation ─► Processor (transform) ─► DB Writer (pooled, upsert)
                │                                                    │
                │                                              PostgreSQL 15
                │                                          (Alembic-managed schema)
                │
          GraphQL API
      (Strawberry + FastAPI)
  ├── Query:        patients, labResults, medications
  └── Subscription: onNewPatient, onNewLabResult, onNewMedication
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| Message Broker | Apache Kafka 7.5.0 (Confluent) |
| Database | PostgreSQL 15 |
| DB Driver & Pool | psycopg3 + psycopg_pool |
| API | FastAPI + Strawberry GraphQL |
| Validation | Pydantic v2 |
| Configuration | pydantic-settings (env vars) |
| Logging | structlog (JSON / console) |
| Migrations | Alembic |
| Data Generation | Faker |
| Containerization | Docker + Docker Compose |

## Project Structure

```
ehr-sync-pipeline/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── .env.example
├── postgres/
│   └── init.sql                        # DB schema (auto-run on container start)
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py       # Initial migration with updated_at columns
├── src/
│   ├── main.py                         # Orchestrator — consumer threads + API server
│   ├── config/
│   │   └── settings.py                 # Centralized settings (pydantic-settings)
│   ├── models/
│   │   ├── patient.py                  # PatientEvent Pydantic model
│   │   ├── lab_result.py               # LabResultEvent Pydantic model
│   │   └── medication.py               # MedicationEvent Pydantic model
│   ├── producers/
│   │   ├── patient_data.py             # Kafka producer — patient events
│   │   ├── lab_results_data.py         # Kafka producer — lab result events
│   │   └── medications_data.py         # Kafka producer — medication events
│   ├── consumers/
│   │   ├── base_consumer.py            # Abstract base — offset mgmt, retry, DLQ
│   │   ├── patient_consumer.py
│   │   ├── lab_consumer.py
│   │   └── medication_consumer.py
│   ├── processor/
│   │   ├── transform.py                # Stream-specific transforms (all 3 types)
│   │   └── validators.py               # Dict → Pydantic model validation
│   ├── writer/
│   │   ├── db_pool.py                  # ConnectionPool singleton (psycopg3)
│   │   └── db_writer.py                # Upsert with timestamp conflict resolution
│   ├── api/
│   │   ├── app.py                      # FastAPI app + Strawberry GraphQL mount
│   │   ├── schema.py                   # GraphQL types, queries, subscriptions
│   │   └── resolvers.py                # Raw SQL resolvers against the pool
│   └── observability/
│       ├── logging.py                  # structlog config + stdlib bridge
│       └── health.py                   # /healthz (liveness) + /readyz (readiness)
└── tests/
    ├── unit/
    │   ├── test_models.py              # Pydantic model validation (27 tests)
    │   ├── test_transform.py           # Transform functions (6 tests)
    │   └── test_validators.py          # Validation utilities (7 tests)
    └── integration/
        └── test_db_writer.py           # Upsert logic against real Postgres (5 tests)
```

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run the Full Pipeline

```bash
# Clone the repository
git clone https://github.com/your-username/EHR-Sync-Pipeline.git
cd EHR-Sync-Pipeline

# Start all services (Postgres, Zookeeper, Kafka, 3 producers, consumer + API)
docker-compose up --build
```

This starts 7 containers:

| Container | Description | Port |
|-----------|-------------|------|
| `ehr-postgres` | PostgreSQL 15 database | 5432 |
| `zookeeper` | Kafka coordination | 2181 |
| `kafka` | Message broker | 9092 |
| `ehr-producer-patient` | Patient event producer | — |
| `ehr-producer-labs` | Lab result event producer | — |
| `ehr-producer-meds` | Medication event producer | — |
| `ehr-consumer` | Consumer pipeline + GraphQL API | 8000 |

### Access the GraphQL API

Once running, open the GraphiQL explorer in your browser:

```
http://localhost:8000/graphql
```

#### Example Queries

**List patients with pagination:**
```graphql
query {
  patients(limit: 10, offset: 0) {
    id
    name
    age
    condition
    updatedAt
  }
}
```

**Get a single patient with related records:**
```graphql
query {
  patient(id: "some-uuid-here") {
    id
    name
    age
    condition
    labResults {
      testCode
      testName
      value
      unit
      resultTime
    }
    medications {
      drugName
      dose
      route
      startTime
      endTime
    }
  }
}
```

**Filter lab results by test code:**
```graphql
query {
  labResults(testCode: "GLU", limit: 5) {
    id
    patientId
    testName
    value
    unit
    resultTime
  }
}
```

**Subscribe to real-time patient events:**
```graphql
subscription {
  onNewPatient {
    id
    name
    age
    condition
  }
}
```

### Health Checks

```bash
# Liveness — is the process alive?
curl http://localhost:8000/healthz

# Readiness — are DB and Kafka reachable?
curl http://localhost:8000/readyz
```

## Configuration

All settings are controlled via environment variables prefixed with `EHR_`. See `.env.example` for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `EHR_DB_HOST` | `postgres` | PostgreSQL hostname |
| `EHR_DB_PORT` | `5432` | PostgreSQL port |
| `EHR_DB_NAME` | `ehr_db` | Database name |
| `EHR_DB_USER` | `postgres` | Database user |
| `EHR_DB_PASSWORD` | `password` | Database password |
| `EHR_DB_POOL_MIN_SIZE` | `2` | Minimum connections in pool |
| `EHR_DB_POOL_MAX_SIZE` | `10` | Maximum connections in pool |
| `EHR_DB_POOL_MAX_IDLE` | `300.0` | Max idle time (seconds) before connection is closed |
| `EHR_KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker address |
| `EHR_KAFKA_CONSUMER_GROUP_PREFIX` | `ehr-pipeline` | Prefix for consumer group IDs |
| `EHR_KAFKA_DLQ_TOPIC` | `ehr.dlq` | Dead-letter queue topic |
| `EHR_KAFKA_MAX_RETRIES` | `3` | Retries before sending to DLQ |
| `EHR_API_HOST` | `0.0.0.0` | API server bind address |
| `EHR_API_PORT` | `8000` | API server port |
| `EHR_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `EHR_LOG_FORMAT` | `json` | Log format (`json` for production, `console` for dev) |

## Database Schema

Three tables with UUID primary keys and timestamp-based upsert logic:

```sql
patients (id UUID PK, name, age, condition, updated_at)
    │
    ├── lab_results (id UUID PK, patient_id FK, test_code, test_name, value, unit, result_time, updated_at)
    │
    └── medications (id UUID PK, patient_id FK, drug_code, drug_name, dose, route, start_time, end_time, ingested_at, updated_at)
```

Writes use `ON CONFLICT (id) DO UPDATE ... WHERE EXCLUDED.updated_at > table.updated_at`, ensuring idempotent last-writer-wins semantics.

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision -m "description_of_change"

# Rollback one step
alembic downgrade -1
```

## Kafka Topics

| Topic | Producer | Consumer Group |
|-------|----------|---------------|
| `ehr.patient.events` | `patient_data.py` | `ehr-pipeline-patients` |
| `ehr.labresults.events` | `lab_results_data.py` | `ehr-pipeline-labs` |
| `ehr.medications.events` | `medications_data.py` | `ehr-pipeline-meds` |
| `ehr.dlq` | Consumer (on failure) | — |

### Consumer Reliability

- **Manual offset commits** — offsets are committed only after successful DB write
- **Retry with exponential backoff** — 3 attempts (1s, 2s, 4s) before sending to DLQ
- **Dead-letter queue** — failed messages go to `ehr.dlq` with error metadata and attempt count
- **Graceful shutdown** — SIGTERM/SIGINT triggers clean consumer close with final offset commit

## Data Validation

All incoming Kafka messages are validated with Pydantic v2 models before processing:

| Model | Key Validations |
|-------|----------------|
| `PatientEvent` | UUID id, non-empty name, age 0-120, condition defaults to "Unknown" |
| `LabResultEvent` | UUID id + patient_id, non-empty test_code, finite numeric value |
| `MedicationEvent` | UUID id + patient_id, non-empty drug_code, route from enum (oral, iv, im, sc, topical, inhaled, subcutaneous) |

## Testing

### Unit Tests (40 tests)

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/unit -v
```

Covers model validation, transform functions, and validation utilities.

### Integration Tests (5 tests)

Requires a running PostgreSQL instance:

```bash
# Start Postgres
docker-compose up postgres -d

# Run integration tests
pytest tests/integration -v -m integration
```

Tests upsert logic including newer-wins and older-ignored conflict resolution.

## Observability

### Structured Logging

All application logging uses `structlog` with JSON output (production) or colored console output (development). Third-party libraries (kafka-python, uvicorn) are bridged through the same pipeline.

```json
{
  "event": "patient_upserted",
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "stream_name": "patients",
  "level": "info",
  "timestamp": "2026-06-14T12:00:00.000000Z"
}
```

Set `EHR_LOG_FORMAT=console` for human-readable dev output.

### Health Endpoints

| Endpoint | Purpose | Checks |
|----------|---------|--------|
| `GET /healthz` | Liveness probe | Process alive (always 200) |
| `GET /readyz` | Readiness probe | DB pool + Kafka reachable (200 or 503) |

## Stopping the Pipeline

```bash
# Graceful shutdown (sends SIGTERM)
docker-compose down

# Remove volumes (wipes database)
docker-compose down -v
```
