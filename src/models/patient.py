"""Pydantic model for patient events consumed from Kafka."""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field


class PatientEvent(BaseModel):
    """Schema for a patient event message."""

    id: UUID
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    condition: str = Field(default="Unknown")
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
