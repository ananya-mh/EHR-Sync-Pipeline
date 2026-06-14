"""Transform functions for all three EHR event streams.

Each function receives a validated Pydantic model instance, applies
stream-specific normalizations, and returns a plain dict ready for the
DB writer.
"""

from src.models.lab_result import LabResultEvent
from src.models.medication import MedicationEvent
from src.models.patient import PatientEvent


def transform_patient(event: PatientEvent) -> dict:
    """Title-case name and condition, then return a DB-ready dict."""
    event.name = event.name.strip().title()
    event.condition = event.condition.strip().title()
    return event.model_dump()


def transform_lab_result(event: LabResultEvent) -> dict:
    """Normalize unit to lowercase and strip test_name whitespace."""
    event.test_name = event.test_name.strip()
    event.unit = event.unit.strip().lower()
    return event.model_dump()


def transform_medication(event: MedicationEvent) -> dict:
    """Strip drug_name whitespace and normalize route to lowercase."""
    event.drug_name = event.drug_name.strip()
    event.route = event.route.strip().lower()
    return event.model_dump()
