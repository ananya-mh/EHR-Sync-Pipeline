"""Pydantic model for medication events consumed from Kafka."""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

VALID_ROUTES = ("oral", "iv", "im", "sc", "topical", "inhaled", "subcutaneous")


class MedicationEvent(BaseModel):
    """Schema for a medication event message."""

    id: UUID
    patient_id: UUID
    drug_code: str = Field(..., min_length=1)
    drug_name: str
    dose: str
    route: Literal["oral", "iv", "im", "sc", "topical", "inhaled", "subcutaneous"]
    start_time: datetime
    end_time: datetime
    ingested_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @field_validator("route", mode="before")
    @classmethod
    def normalize_route(cls, v: str) -> str:
        """Accept routes case-insensitively and normalize to lowercase."""
        if isinstance(v, str):
            return v.strip().lower()
        return v
