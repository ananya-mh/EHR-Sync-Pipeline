"""Kafka consumer for patient EHR events."""

from __future__ import annotations

import threading
from typing import Type

from pydantic import BaseModel

from src.consumers.base_consumer import BaseConsumer
from src.models.patient import PatientEvent


class PatientConsumer(BaseConsumer):
    """Consumer that reads and processes patient events from Kafka."""

    def __init__(self, shutdown_event: threading.Event) -> None:
        """Initialise the patient consumer."""
        super().__init__(shutdown_event)

    @property
    def topic(self) -> str:
        """Kafka topic for patient events."""
        return "ehr.patient.events"

    @property
    def group_id(self) -> str:
        """Consumer group for the patient pipeline."""
        return "ehr-pipeline-patients"

    @property
    def model_class(self) -> Type[BaseModel]:
        """Pydantic model for patient event validation."""
        return PatientEvent
