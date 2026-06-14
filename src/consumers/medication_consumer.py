"""Kafka consumer for medication EHR events."""

from __future__ import annotations

import threading
from typing import Type

from pydantic import BaseModel

from src.consumers.base_consumer import BaseConsumer
from src.models.medication import MedicationEvent


class MedicationConsumer(BaseConsumer):
    """Consumer that reads and processes medication events from Kafka."""

    def __init__(self, shutdown_event: threading.Event) -> None:
        """Initialise the medication consumer."""
        super().__init__(shutdown_event)

    @property
    def topic(self) -> str:
        """Kafka topic for medication events."""
        return "ehr.medications.events"

    @property
    def group_id(self) -> str:
        """Consumer group for the medications pipeline."""
        return "ehr-pipeline-meds"

    @property
    def model_class(self) -> Type[BaseModel]:
        """Pydantic model for medication event validation."""
        return MedicationEvent
