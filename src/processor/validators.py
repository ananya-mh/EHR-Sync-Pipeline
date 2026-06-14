"""Validation utilities that parse raw dicts into typed Pydantic models.

Each function wraps ``model_validate`` and lets ``ValidationError``
propagate so callers (consumers, tests) get actionable diagnostics.
"""

from src.models.lab_result import LabResultEvent
from src.models.medication import MedicationEvent
from src.models.patient import PatientEvent


def validate_patient(data: dict) -> PatientEvent:
    """Parse a raw dict into a validated PatientEvent."""
    return PatientEvent.model_validate(data)


def validate_lab_result(data: dict) -> LabResultEvent:
    """Parse a raw dict into a validated LabResultEvent."""
    return LabResultEvent.model_validate(data)


def validate_medication(data: dict) -> MedicationEvent:
    """Parse a raw dict into a validated MedicationEvent."""
    return MedicationEvent.model_validate(data)
