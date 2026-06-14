"""Database query resolvers for the GraphQL API layer.

Each function executes parameterized SQL against the connection pool and
returns results as dictionaries suitable for constructing Strawberry types.
"""

from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row

from src.writer.db_pool import get_pool


def fetch_patients(
    limit: int = 20,
    offset: int = 0,
    condition: str | None = None,
) -> list[dict[str, Any]]:
    """Return a paginated list of patients, optionally filtered by condition."""
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if condition is not None:
                cur.execute(
                    "SELECT id, name, age, condition, updated_at "
                    "FROM patients "
                    "WHERE condition = %(condition)s "
                    "ORDER BY updated_at DESC "
                    "LIMIT %(limit)s OFFSET %(offset)s",
                    {"condition": condition, "limit": limit, "offset": offset},
                )
            else:
                cur.execute(
                    "SELECT id, name, age, condition, updated_at "
                    "FROM patients "
                    "ORDER BY updated_at DESC "
                    "LIMIT %(limit)s OFFSET %(offset)s",
                    {"limit": limit, "offset": offset},
                )
            return cur.fetchall()


def fetch_patient_by_id(patient_id: str) -> dict[str, Any] | None:
    """Return a single patient by primary key, or None if not found."""
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, name, age, condition, updated_at "
                "FROM patients "
                "WHERE id = %(patient_id)s",
                {"patient_id": patient_id},
            )
            return cur.fetchone()


def fetch_lab_results(
    limit: int = 20,
    offset: int = 0,
    patient_id: str | None = None,
    test_code: str | None = None,
) -> list[dict[str, Any]]:
    """Return a paginated list of lab results with optional filters."""
    pool = get_pool()
    conditions: list[str] = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if patient_id is not None:
        conditions.append("patient_id = %(patient_id)s")
        params["patient_id"] = patient_id

    if test_code is not None:
        conditions.append("test_code = %(test_code)s")
        params["test_code"] = test_code

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, patient_id, test_code, test_name, "
                "value, unit, result_time, updated_at "
                f"FROM lab_results {where_clause} "
                "ORDER BY result_time DESC "
                "LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall()


def fetch_lab_results_for_patient(patient_id: str) -> list[dict[str, Any]]:
    """Return all lab results belonging to a specific patient."""
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, patient_id, test_code, test_name, "
                "value, unit, result_time, updated_at "
                "FROM lab_results "
                "WHERE patient_id = %(patient_id)s "
                "ORDER BY result_time DESC",
                {"patient_id": patient_id},
            )
            return cur.fetchall()


def fetch_medications(
    limit: int = 20,
    offset: int = 0,
    patient_id: str | None = None,
    drug_code: str | None = None,
) -> list[dict[str, Any]]:
    """Return a paginated list of medications with optional filters."""
    pool = get_pool()
    conditions: list[str] = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if patient_id is not None:
        conditions.append("patient_id = %(patient_id)s")
        params["patient_id"] = patient_id

    if drug_code is not None:
        conditions.append("drug_code = %(drug_code)s")
        params["drug_code"] = drug_code

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, patient_id, drug_code, drug_name, "
                "dose, route, start_time, end_time, ingested_at, updated_at "
                f"FROM medications {where_clause} "
                "ORDER BY start_time DESC "
                "LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall()


def fetch_medications_for_patient(patient_id: str) -> list[dict[str, Any]]:
    """Return all medications belonging to a specific patient."""
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, patient_id, drug_code, drug_name, "
                "dose, route, start_time, end_time, ingested_at, updated_at "
                "FROM medications "
                "WHERE patient_id = %(patient_id)s "
                "ORDER BY start_time DESC",
                {"patient_id": patient_id},
            )
            return cur.fetchall()
