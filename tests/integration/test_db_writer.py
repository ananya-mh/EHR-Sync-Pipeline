"""Integration tests for the database writer upsert logic.

These tests require a running PostgreSQL instance. Connection details are
read from environment variables (EHR_DB_HOST, etc.) with defaults matching
docker-compose.yml. Run with: pytest -m integration tests/integration/
"""

import os
import uuid
from datetime import datetime, timezone, timedelta

import psycopg
import pytest

from src.writer.db_writer import upsert_patient, upsert_lab_result, upsert_medication


def _get_test_conninfo() -> str:
    """Build a connection string for the test database."""
    host = os.environ.get("EHR_DB_HOST", "localhost")
    port = os.environ.get("EHR_DB_PORT", "5432")
    dbname = os.environ.get("EHR_DB_NAME", "ehr_db")
    user = os.environ.get("EHR_DB_USER", "postgres")
    password = os.environ.get("EHR_DB_PASSWORD", "password")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


@pytest.fixture(scope="session")
def db_conn() -> psycopg.Connection:
    """Create a test database connection that persists for the test session."""
    conninfo = _get_test_conninfo()
    conn = psycopg.connect(conninfo, autocommit=True)

    # Ensure tables exist with the updated_at column.
    conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            age INT CHECK (age BETWEEN 0 AND 120),
            condition TEXT,
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lab_results (
            id UUID PRIMARY KEY,
            patient_id UUID REFERENCES patients(id),
            test_code TEXT,
            test_name TEXT,
            value NUMERIC,
            unit TEXT,
            result_time TIMESTAMPTZ,
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id UUID PRIMARY KEY,
            patient_id UUID REFERENCES patients(id),
            drug_code TEXT,
            drug_name TEXT,
            dose TEXT,
            route TEXT,
            start_time TIMESTAMPTZ,
            end_time TIMESTAMPTZ,
            ingested_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_tables(db_conn: psycopg.Connection) -> None:
    """Truncate all tables before each test to ensure isolation."""
    db_conn.execute("TRUNCATE medications, lab_results, patients CASCADE")


@pytest.mark.integration
def test_insert_patient(db_conn: psycopg.Connection) -> None:
    """A new patient should be inserted successfully."""
    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    data = {
        "id": str(patient_id),
        "name": "Jane Doe",
        "age": 34,
        "condition": "Healthy",
        "updated_at": now.isoformat(),
    }

    upsert_patient(data)

    row = db_conn.execute(
        "SELECT id, name, age, condition FROM patients WHERE id = %s",
        (str(patient_id),),
    ).fetchone()
    assert row is not None
    assert row[1] == "Jane Doe"
    assert row[2] == 34
    assert row[3] == "Healthy"


@pytest.mark.integration
def test_upsert_patient_newer_wins(db_conn: psycopg.Connection) -> None:
    """An upsert with a newer updated_at should overwrite the existing row."""
    patient_id = uuid.uuid4()
    old_time = datetime.now(timezone.utc) - timedelta(hours=1)
    new_time = datetime.now(timezone.utc)

    original = {
        "id": str(patient_id),
        "name": "Original Name",
        "age": 30,
        "condition": "Flu",
        "updated_at": old_time.isoformat(),
    }
    upsert_patient(original)

    updated = {
        "id": str(patient_id),
        "name": "Updated Name",
        "age": 31,
        "condition": "Recovered",
        "updated_at": new_time.isoformat(),
    }
    upsert_patient(updated)

    row = db_conn.execute(
        "SELECT name, age, condition FROM patients WHERE id = %s",
        (str(patient_id),),
    ).fetchone()
    assert row is not None
    assert row[0] == "Updated Name"
    assert row[1] == 31
    assert row[2] == "Recovered"


@pytest.mark.integration
def test_upsert_patient_older_ignored(db_conn: psycopg.Connection) -> None:
    """An upsert with an older updated_at should leave the existing row unchanged."""
    patient_id = uuid.uuid4()
    old_time = datetime.now(timezone.utc) - timedelta(hours=1)
    new_time = datetime.now(timezone.utc)

    # Insert with the newer timestamp first.
    original = {
        "id": str(patient_id),
        "name": "Current Name",
        "age": 45,
        "condition": "Diabetes",
        "updated_at": new_time.isoformat(),
    }
    upsert_patient(original)

    # Attempt to upsert with an older timestamp.
    stale = {
        "id": str(patient_id),
        "name": "Stale Name",
        "age": 44,
        "condition": "Unknown",
        "updated_at": old_time.isoformat(),
    }
    upsert_patient(stale)

    row = db_conn.execute(
        "SELECT name, age, condition FROM patients WHERE id = %s",
        (str(patient_id),),
    ).fetchone()
    assert row is not None
    assert row[0] == "Current Name"
    assert row[1] == 45
    assert row[2] == "Diabetes"


@pytest.mark.integration
def test_insert_lab_result(db_conn: psycopg.Connection) -> None:
    """A new lab result should be inserted with its parent patient."""
    patient_id = uuid.uuid4()
    lab_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Insert parent patient first.
    upsert_patient({
        "id": str(patient_id),
        "name": "Lab Patient",
        "age": 50,
        "condition": "Testing",
        "updated_at": now.isoformat(),
    })

    lab_data = {
        "id": str(lab_id),
        "patient_id": str(patient_id),
        "test_code": "CBC",
        "test_name": "Complete Blood Count",
        "value": 7.5,
        "unit": "g/dL",
        "result_time": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    upsert_lab_result(lab_data)

    row = db_conn.execute(
        "SELECT id, patient_id, test_code, test_name, value, unit FROM lab_results WHERE id = %s",
        (str(lab_id),),
    ).fetchone()
    assert row is not None
    assert row[2] == "CBC"
    assert row[3] == "Complete Blood Count"
    assert float(row[4]) == 7.5
    assert row[5] == "g/dL"


@pytest.mark.integration
def test_insert_medication(db_conn: psycopg.Connection) -> None:
    """A new medication should be inserted with its parent patient."""
    patient_id = uuid.uuid4()
    med_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    end_time = now + timedelta(days=7)

    # Insert parent patient first.
    upsert_patient({
        "id": str(patient_id),
        "name": "Med Patient",
        "age": 60,
        "condition": "Hypertension",
        "updated_at": now.isoformat(),
    })

    med_data = {
        "id": str(med_id),
        "patient_id": str(patient_id),
        "drug_code": "LISINOPRIL",
        "drug_name": "Lisinopril",
        "dose": "10mg",
        "route": "oral",
        "start_time": now.isoformat(),
        "end_time": end_time.isoformat(),
        "ingested_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    upsert_medication(med_data)

    row = db_conn.execute(
        "SELECT id, patient_id, drug_code, drug_name, dose, route FROM medications WHERE id = %s",
        (str(med_id),),
    ).fetchone()
    assert row is not None
    assert row[2] == "LISINOPRIL"
    assert row[3] == "Lisinopril"
    assert row[4] == "10mg"
    assert row[5] == "oral"
