"""GraphQL schema definition using Strawberry.

Defines Strawberry types for patients, lab results, and medications, along
with query resolvers and Kafka-backed subscriptions for real-time streaming.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
from uuid import uuid4

import strawberry
import structlog
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from src.api.resolvers import (
    fetch_lab_results,
    fetch_lab_results_for_patient,
    fetch_medications,
    fetch_medications_for_patient,
    fetch_patient_by_id,
    fetch_patients,
)
from src.config.settings import settings

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Strawberry GraphQL types
# ---------------------------------------------------------------------------


@strawberry.type
class LabResultType:
    """GraphQL type representing a single lab result record."""

    id: strawberry.ID
    patient_id: strawberry.ID
    test_code: str
    test_name: str
    value: float
    unit: str
    result_time: datetime
    updated_at: datetime | None


@strawberry.type
class MedicationType:
    """GraphQL type representing a single medication record."""

    id: strawberry.ID
    patient_id: strawberry.ID
    drug_code: str
    drug_name: str
    dose: str
    route: str
    start_time: datetime
    end_time: datetime
    ingested_at: datetime | None
    updated_at: datetime | None


@strawberry.type
class PatientType:
    """GraphQL type representing a patient with lazy-loaded relations."""

    id: strawberry.ID
    name: str
    age: int
    condition: str
    updated_at: datetime | None

    @strawberry.field
    def lab_results(self) -> list[LabResultType] | None:
        """Lazily resolve lab results belonging to this patient."""
        rows = fetch_lab_results_for_patient(str(self.id))
        if not rows:
            return None
        return [
            LabResultType(
                id=strawberry.ID(str(row["id"])),
                patient_id=strawberry.ID(str(row["patient_id"])),
                test_code=row["test_code"],
                test_name=row["test_name"],
                value=float(row["value"]),
                unit=row["unit"],
                result_time=row["result_time"],
                updated_at=row.get("updated_at"),
            )
            for row in rows
        ]

    @strawberry.field
    def medications(self) -> list[MedicationType] | None:
        """Lazily resolve medications belonging to this patient."""
        rows = fetch_medications_for_patient(str(self.id))
        if not rows:
            return None
        return [
            MedicationType(
                id=strawberry.ID(str(row["id"])),
                patient_id=strawberry.ID(str(row["patient_id"])),
                drug_code=row["drug_code"],
                drug_name=row["drug_name"],
                dose=row["dose"],
                route=row["route"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                ingested_at=row.get("ingested_at"),
                updated_at=row.get("updated_at"),
            )
            for row in rows
        ]


# ---------------------------------------------------------------------------
# Helper constructors
# ---------------------------------------------------------------------------


def _patient_from_row(row: dict) -> PatientType:
    """Build a PatientType from a database row dictionary."""
    return PatientType(
        id=strawberry.ID(str(row["id"])),
        name=row["name"],
        age=row["age"],
        condition=row["condition"],
        updated_at=row.get("updated_at"),
    )


def _lab_result_from_row(row: dict) -> LabResultType:
    """Build a LabResultType from a database row dictionary."""
    return LabResultType(
        id=strawberry.ID(str(row["id"])),
        patient_id=strawberry.ID(str(row["patient_id"])),
        test_code=row["test_code"],
        test_name=row["test_name"],
        value=float(row["value"]),
        unit=row["unit"],
        result_time=row["result_time"],
        updated_at=row.get("updated_at"),
    )


def _medication_from_row(row: dict) -> MedicationType:
    """Build a MedicationType from a database row dictionary."""
    return MedicationType(
        id=strawberry.ID(str(row["id"])),
        patient_id=strawberry.ID(str(row["patient_id"])),
        drug_code=row["drug_code"],
        drug_name=row["drug_name"],
        dose=row["dose"],
        route=row["route"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        ingested_at=row.get("ingested_at"),
        updated_at=row.get("updated_at"),
    )


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


@strawberry.type
class Query:
    """Root query type for the EHR GraphQL API."""

    @strawberry.field
    def patients(
        self,
        limit: int = 20,
        offset: int = 0,
        condition: str | None = None,
    ) -> list[PatientType]:
        """Return a paginated list of patients, optionally filtered by condition."""
        rows = fetch_patients(limit=limit, offset=offset, condition=condition)
        return [_patient_from_row(row) for row in rows]

    @strawberry.field
    def patient(self, id: strawberry.ID) -> PatientType | None:
        """Return a single patient by ID with related lab results and medications."""
        row = fetch_patient_by_id(str(id))
        if row is None:
            return None
        return _patient_from_row(row)

    @strawberry.field
    def lab_results(
        self,
        limit: int = 20,
        offset: int = 0,
        patient_id: strawberry.ID | None = None,
        test_code: str | None = None,
    ) -> list[LabResultType]:
        """Return a paginated list of lab results with optional filters."""
        pid = str(patient_id) if patient_id is not None else None
        rows = fetch_lab_results(
            limit=limit, offset=offset, patient_id=pid, test_code=test_code,
        )
        return [_lab_result_from_row(row) for row in rows]

    @strawberry.field
    def medications(
        self,
        limit: int = 20,
        offset: int = 0,
        patient_id: strawberry.ID | None = None,
        drug_code: str | None = None,
    ) -> list[MedicationType]:
        """Return a paginated list of medications with optional filters."""
        pid = str(patient_id) if patient_id is not None else None
        rows = fetch_medications(
            limit=limit, offset=offset, patient_id=pid, drug_code=drug_code,
        )
        return [_medication_from_row(row) for row in rows]


# ---------------------------------------------------------------------------
# Subscriptions (Kafka-backed)
# ---------------------------------------------------------------------------


async def _kafka_subscription(
    topic: str,
    group_prefix: str,
) -> AsyncGenerator[dict, None]:
    """Yield deserialized messages from a Kafka topic as an async generator.

    Each subscriber gets a unique consumer group so that every active
    GraphQL subscription receives all messages independently.
    """
    group_id = f"{group_prefix}-{uuid4()}"
    consumer: KafkaConsumer | None = None
    log = logger.bind(topic=topic, group_id=group_id)

    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=1000,
            api_version=(0, 10, 1),
        )
        log.info("subscription.consumer_started")

        while True:
            records = consumer.poll(timeout_ms=500)
            for _tp, messages in records.items():
                for message in messages:
                    yield message.value
            # Yield control back to the event loop between polls so the
            # subscription can be cancelled and other coroutines can run.
            await asyncio.sleep(0.1)

    except KafkaError as exc:
        log.error("subscription.kafka_error", error=str(exc))
        raise
    finally:
        if consumer is not None:
            consumer.close()
            log.info("subscription.consumer_closed")


@strawberry.type
class Subscription:
    """Root subscription type for real-time EHR event streaming."""

    @strawberry.subscription
    async def on_new_patient(self) -> AsyncGenerator[PatientType, None]:
        """Stream new patient events from Kafka in real time."""
        async for data in _kafka_subscription(
            topic="ehr.patient.events",
            group_prefix="graphql-sub-patients",
        ):
            yield PatientType(
                id=strawberry.ID(str(data["id"])),
                name=data["name"],
                age=data["age"],
                condition=data.get("condition", "Unknown"),
                updated_at=None,
            )

    @strawberry.subscription
    async def on_new_lab_result(self) -> AsyncGenerator[LabResultType, None]:
        """Stream new lab result events from Kafka in real time."""
        async for data in _kafka_subscription(
            topic="ehr.labresults.events",
            group_prefix="graphql-sub-labs",
        ):
            result_time = data["result_time"]
            if isinstance(result_time, str):
                result_time = datetime.fromisoformat(result_time)

            yield LabResultType(
                id=strawberry.ID(str(data["id"])),
                patient_id=strawberry.ID(str(data["patient_id"])),
                test_code=data["test_code"],
                test_name=data["test_name"],
                value=float(data["value"]),
                unit=data["unit"],
                result_time=result_time,
                updated_at=None,
            )

    @strawberry.subscription
    async def on_new_medication(self) -> AsyncGenerator[MedicationType, None]:
        """Stream new medication events from Kafka in real time."""
        async for data in _kafka_subscription(
            topic="ehr.medications.events",
            group_prefix="graphql-sub-meds",
        ):
            start_time = data["start_time"]
            end_time = data["end_time"]
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)

            yield MedicationType(
                id=strawberry.ID(str(data["id"])),
                patient_id=strawberry.ID(str(data["patient_id"])),
                drug_code=data["drug_code"],
                drug_name=data["drug_name"],
                dose=data["dose"],
                route=data["route"],
                start_time=start_time,
                end_time=end_time,
                ingested_at=None,
                updated_at=None,
            )


# ---------------------------------------------------------------------------
# Schema instance
# ---------------------------------------------------------------------------

schema = strawberry.Schema(query=Query, subscription=Subscription)
