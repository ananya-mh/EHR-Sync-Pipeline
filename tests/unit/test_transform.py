"""Unit tests for the processor transform functions."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.models.lab_result import LabResultEvent
from src.models.medication import MedicationEvent
from src.models.patient import PatientEvent
from src.processor.transform import (
    transform_lab_result,
    transform_medication,
    transform_patient,
)


# -- Patient transforms -------------------------------------------------------


def _make_patient(**overrides: object) -> PatientEvent:
    """Build a PatientEvent with sensible defaults, overridden by kwargs."""
    defaults: dict = {
        "id": uuid4(),
        "name": "john doe",
        "age": 35,
        "condition": "diabetes",
    }
    defaults.update(overrides)
    return PatientEvent.model_validate(defaults)


def test_transform_patient_title_cases_name() -> None:
    """Name 'john doe' should become 'John Doe'."""
    result = transform_patient(_make_patient(name="john doe"))
    assert result["name"] == "John Doe"


def test_transform_patient_title_cases_condition() -> None:
    """Condition 'diabetes' should become 'Diabetes'."""
    result = transform_patient(_make_patient(condition="diabetes"))
    assert result["condition"] == "Diabetes"


# -- Lab result transforms ----------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _make_lab_result(**overrides: object) -> LabResultEvent:
    """Build a LabResultEvent with sensible defaults."""
    defaults: dict = {
        "id": uuid4(),
        "patient_id": uuid4(),
        "test_code": "GLU",
        "test_name": "Glucose",
        "value": 95.0,
        "unit": "mg/dL",
        "result_time": _NOW.isoformat(),
    }
    defaults.update(overrides)
    return LabResultEvent.model_validate(defaults)


def test_transform_lab_result_normalizes_unit() -> None:
    """Unit 'MG/DL' should become 'mg/dl'."""
    result = transform_lab_result(_make_lab_result(unit="MG/DL"))
    assert result["unit"] == "mg/dl"


def test_transform_lab_result_strips_test_name() -> None:
    """Whitespace around test_name should be stripped."""
    result = transform_lab_result(_make_lab_result(test_name="  Glucose  "))
    assert result["test_name"] == "Glucose"


# -- Medication transforms ----------------------------------------------------


def _make_medication(**overrides: object) -> MedicationEvent:
    """Build a MedicationEvent with sensible defaults."""
    defaults: dict = {
        "id": uuid4(),
        "patient_id": uuid4(),
        "drug_code": "AMOX",
        "drug_name": "Amoxicillin",
        "dose": "500mg",
        "route": "oral",
        "start_time": _NOW.isoformat(),
        "end_time": _NOW.isoformat(),
    }
    defaults.update(overrides)
    return MedicationEvent.model_validate(defaults)


def test_transform_medication_strips_drug_name() -> None:
    """Whitespace around drug_name should be stripped."""
    result = transform_medication(_make_medication(drug_name="  Amoxicillin  "))
    assert result["drug_name"] == "Amoxicillin"


def test_transform_medication_normalizes_route() -> None:
    """Route 'Oral' should become 'oral'."""
    result = transform_medication(_make_medication(route="Oral"))
    assert result["route"] == "oral"
