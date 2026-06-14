"""Database writer with upsert logic and timestamp-based conflict resolution.

Each upsert function uses ON CONFLICT (id) DO UPDATE with a WHERE clause
that only applies the update when the incoming updated_at is newer than
the existing row, ensuring idempotent writes and last-writer-wins semantics.
"""

import psycopg

import structlog

from src.writer.db_pool import get_pool

logger = structlog.get_logger(__name__)


def upsert_patient(data: dict) -> None:
    """Insert or update a patient record if the incoming timestamp is newer."""
    pool = get_pool()
    sql = """
        INSERT INTO patients (id, name, age, condition, updated_at)
        VALUES (%(id)s, %(name)s, %(age)s, %(condition)s, %(updated_at)s)
        ON CONFLICT (id) DO UPDATE SET
            name       = EXCLUDED.name,
            age        = EXCLUDED.age,
            condition  = EXCLUDED.condition,
            updated_at = EXCLUDED.updated_at
        WHERE EXCLUDED.updated_at > patients.updated_at
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, data)
        conn.commit()
    logger.info(
        "patient_upserted",
        patient_id=str(data.get("id")),
    )


def upsert_lab_result(data: dict) -> None:
    """Insert or update a lab result record if the incoming timestamp is newer."""
    pool = get_pool()
    sql = """
        INSERT INTO lab_results (id, patient_id, test_code, test_name, value, unit, result_time, updated_at)
        VALUES (%(id)s, %(patient_id)s, %(test_code)s, %(test_name)s, %(value)s, %(unit)s, %(result_time)s, %(updated_at)s)
        ON CONFLICT (id) DO UPDATE SET
            patient_id  = EXCLUDED.patient_id,
            test_code   = EXCLUDED.test_code,
            test_name   = EXCLUDED.test_name,
            value       = EXCLUDED.value,
            unit        = EXCLUDED.unit,
            result_time = EXCLUDED.result_time,
            updated_at  = EXCLUDED.updated_at
        WHERE EXCLUDED.updated_at > lab_results.updated_at
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, data)
        conn.commit()
    logger.info(
        "lab_result_upserted",
        lab_result_id=str(data.get("id")),
        patient_id=str(data.get("patient_id")),
    )


def upsert_medication(data: dict) -> None:
    """Insert or update a medication record if the incoming timestamp is newer."""
    pool = get_pool()
    sql = """
        INSERT INTO medications (id, patient_id, drug_code, drug_name, dose, route, start_time, end_time, ingested_at, updated_at)
        VALUES (%(id)s, %(patient_id)s, %(drug_code)s, %(drug_name)s, %(dose)s, %(route)s, %(start_time)s, %(end_time)s, %(ingested_at)s, %(updated_at)s)
        ON CONFLICT (id) DO UPDATE SET
            patient_id  = EXCLUDED.patient_id,
            drug_code   = EXCLUDED.drug_code,
            drug_name   = EXCLUDED.drug_name,
            dose        = EXCLUDED.dose,
            route       = EXCLUDED.route,
            start_time  = EXCLUDED.start_time,
            end_time    = EXCLUDED.end_time,
            ingested_at = EXCLUDED.ingested_at,
            updated_at  = EXCLUDED.updated_at
        WHERE EXCLUDED.updated_at > medications.updated_at
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, data)
        conn.commit()
    logger.info(
        "medication_upserted",
        medication_id=str(data.get("id")),
        patient_id=str(data.get("patient_id")),
    )
