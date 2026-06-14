"""Unit tests for the processor validation functions."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.processor.validators import (
    validate_lab_result,
    validate_medication,
    validate_patient,
)


# -- Patient validation -------------------------------------------------------

_NOW = datetime.now(timezone.utc).isoformat()


def _patient_data(**overrides: object) -> dict:
    """Return a valid patient dict, with optional overrides."""
    data: dict = {
        "id": str(uuid4()),
        "name": "Jane Smith",
        "age": 30,
        "condition": "asthma",
    }
    data.update(overrides)
    return data


def test_validate_patient_valid() -> None:
    """A well-formed patient dict should parse without errors."""
    event = validate_patient(_patient_data())
    assert event.name == "Jane Smith"
    assert event.age == 30


def test_validate_patient_empty_name_fails() -> None:
    """An empty name must be rejected."""
    with pytest.raises(ValidationError):
        validate_patient(_patient_data(name=""))


def test_validate_patient_age_out_of_range() -> None:
    """Age 150 exceeds the allowed maximum of 120."""
    with pytest.raises(ValidationError):
        validate_patient(_patient_data(age=150))


# -- Lab result validation -----------------------------------------------------


def _lab_result_data(**overrides: object) -> dict:
    """Return a valid lab result dict, with optional overrides."""
    data: dict = {
        "id": str(uuid4()),
        "patient_id": str(uuid4()),
        "test_code": "GLU",
        "test_name": "Glucose",
        "value": 95.0,
        "unit": "mg/dL",
        "result_time": _NOW,
    }
    data.update(overrides)
    return data


def test_validate_lab_result_valid() -> None:
    """A well-formed lab result dict should parse without errors."""
    event = validate_lab_result(_lab_result_data())
    assert event.test_code == "GLU"


def test_validate_lab_result_empty_test_code_fails() -> None:
    """An empty test_code must be rejected."""
    with pytest.raises(ValidationError):
        validate_lab_result(_lab_result_data(test_code=""))


# -- Medication validation -----------------------------------------------------


def _medication_data(**overrides: object) -> dict:
    """Return a valid medication dict, with optional overrides."""
    data: dict = {
        "id": str(uuid4()),
        "patient_id": str(uuid4()),
        "drug_code": "AMOX",
        "drug_name": "Amoxicillin",
        "dose": "500mg",
        "route": "oral",
        "start_time": _NOW,
        "end_time": _NOW,
    }
    data.update(overrides)
    return data


def test_validate_medication_valid() -> None:
    """A well-formed medication dict should parse without errors."""
    event = validate_medication(_medication_data())
    assert event.drug_code == "AMOX"


def test_validate_medication_invalid_route() -> None:
    """Route 'intravenous' is not in the allowed literal set."""
    with pytest.raises(ValidationError):
        validate_medication(_medication_data(route="intravenous"))
