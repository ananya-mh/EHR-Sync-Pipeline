"""Pydantic model for lab result events consumed from Kafka."""

import math
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LabResultEvent(BaseModel):
    """Schema for a lab result event message."""

    id: UUID
    patient_id: UUID
    test_code: str = Field(..., min_length=1)
    test_name: str
    value: float
    unit: str
    result_time: datetime
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, v: float) -> float:
        """Reject NaN and infinite lab values."""
        if not math.isfinite(v):
            raise ValueError("value must be a finite number")
        return v
