"""Kafka consumer for lab result EHR events."""

from __future__ import annotations

import threading
from typing import Type

from pydantic import BaseModel

from src.consumers.base_consumer import BaseConsumer
from src.models.lab_result import LabResultEvent


class LabConsumer(BaseConsumer):
    """Consumer that reads and processes lab result events from Kafka."""

    def __init__(self, shutdown_event: threading.Event) -> None:
        """Initialise the lab result consumer."""
        super().__init__(shutdown_event)

    @property
    def topic(self) -> str:
        """Kafka topic for lab result events."""
        return "ehr.labresults.events"

    @property
    def group_id(self) -> str:
        """Consumer group for the lab results pipeline."""
        return "ehr-pipeline-labs"

    @property
    def model_class(self) -> Type[BaseModel]:
        """Pydantic model for lab result event validation."""
        return LabResultEvent
