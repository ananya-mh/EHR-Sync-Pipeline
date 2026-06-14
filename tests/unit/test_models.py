"""Unit tests for Pydantic model validation across all event types."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.models.lab_result import LabResultEvent
from src.models.medication import MedicationEvent
from src.models.patient import PatientEvent

_NOW = datetime.now(timezone.utc)
_NOW_ISO = _NOW.isoformat()


# =============================================================================
# PatientEvent
# =============================================================================


def _patient_kwargs(**overrides: object) -> dict:
    """Return valid PatientEvent constructor kwargs."""
    data: dict = {
        "id": uuid4(),
        "name": "Ada Lovelace",
        "age": 36,
        "condition": "healthy",
    }
    data.update(overrides)
    return data


class TestPatientEvent:
    """Tests for PatientEvent model validation."""

    def test_valid_patient(self) -> None:
        """All required fields present with valid values."""
        patient = PatientEvent(**_patient_kwargs())
        assert isinstance(patient.id, UUID)
        assert patient.name == "Ada Lovelace"

    def test_age_boundary_zero(self) -> None:
        """Age 0 is the lower boundary and should be accepted."""
        patient = PatientEvent(**_patient_kwargs(age=0))
        assert patient.age == 0

    def test_age_boundary_120(self) -> None:
        """Age 120 is the upper boundary and should be accepted."""
        patient = PatientEvent(**_patient_kwargs(age=120))
        assert patient.age == 120

    def test_age_below_range_rejected(self) -> None:
        """Negative age must be rejected."""
        with pytest.raises(ValidationError):
            PatientEvent(**_patient_kwargs(age=-1))

    def test_age_above_range_rejected(self) -> None:
        """Age above 120 must be rejected."""
        with pytest.raises(ValidationError):
            PatientEvent(**_patient_kwargs(age=121))

    def test_uuid_from_string(self) -> None:
        """A valid UUID string should be parsed into a UUID object."""
        uid = str(uuid4())
        patient = PatientEvent(**_patient_kwargs(id=uid))
        assert isinstance(patient.id, UUID)
        assert str(patient.id) == uid

    def test_invalid_uuid_rejected(self) -> None:
        """A malformed UUID string must be rejected."""
        with pytest.raises(ValidationError):
            PatientEvent(**_patient_kwargs(id="not-a-uuid"))

    def test_empty_name_rejected(self) -> None:
        """Name must have min_length=1."""
        with pytest.raises(ValidationError):
            PatientEvent(**_patient_kwargs(name=""))

    def test_condition_defaults_to_unknown(self) -> None:
        """When condition is omitted it should default to 'Unknown'."""
        kwargs = _patient_kwargs()
        del kwargs["condition"]
        patient = PatientEvent(**kwargs)
        assert patient.condition == "Unknown"

    def test_updated_at_defaults_to_now(self) -> None:
        """updated_at should auto-populate with a recent UTC datetime."""
        patient = PatientEvent(**_patient_kwargs())
        assert patient.updated_at is not None
        assert patient.updated_at.tzinfo is not None

    def test_datetime_parsed_from_iso_string(self) -> None:
        """updated_at should accept an ISO-8601 string."""
        patient = PatientEvent(**_patient_kwargs(updated_at=_NOW_ISO))
        assert isinstance(patient.updated_at, datetime)


# =============================================================================
# LabResultEvent
# =============================================================================


def _lab_kwargs(**overrides: object) -> dict:
    """Return valid LabResultEvent constructor kwargs."""
    data: dict = {
        "id": uuid4(),
        "patient_id": uuid4(),
        "test_code": "HB",
        "test_name": "Hemoglobin",
        "value": 14.5,
        "unit": "g/dL",
        "result_time": _NOW_ISO,
    }
    data.update(overrides)
    return data


class TestLabResultEvent:
    """Tests for LabResultEvent model validation."""

    def test_valid_lab_result(self) -> None:
        """All required fields present with valid values."""
        lab = LabResultEvent(**_lab_kwargs())
        assert lab.test_code == "HB"
        assert lab.value == 14.5

    def test_uuid_fields_parsed(self) -> None:
        """Both id and patient_id should be UUID objects."""
        lab = LabResultEvent(**_lab_kwargs())
        assert isinstance(lab.id, UUID)
        assert isinstance(lab.patient_id, UUID)

    def test_invalid_patient_id_rejected(self) -> None:
        """A malformed patient_id must be rejected."""
        with pytest.raises(ValidationError):
            LabResultEvent(**_lab_kwargs(patient_id="bad"))

    def test_empty_test_code_rejected(self) -> None:
        """test_code must have min_length=1."""
        with pytest.raises(ValidationError):
            LabResultEvent(**_lab_kwargs(test_code=""))

    def test_nan_value_rejected(self) -> None:
        """NaN is not a finite number and must be rejected."""
        with pytest.raises(ValidationError):
            LabResultEvent(**_lab_kwargs(value=float("nan")))

    def test_inf_value_rejected(self) -> None:
        """Infinity is not a finite number and must be rejected."""
        with pytest.raises(ValidationError):
            LabResultEvent(**_lab_kwargs(value=float("inf")))

    def test_result_time_parsed_from_iso(self) -> None:
        """result_time should accept an ISO-8601 string."""
        lab = LabResultEvent(**_lab_kwargs())
        assert isinstance(lab.result_time, datetime)

    def test_updated_at_defaults_to_now(self) -> None:
        """updated_at should auto-populate with a recent UTC datetime."""
        lab = LabResultEvent(**_lab_kwargs())
        assert lab.updated_at is not None


# =============================================================================
# MedicationEvent
# =============================================================================


def _med_kwargs(**overrides: object) -> dict:
    """Return valid MedicationEvent constructor kwargs."""
    data: dict = {
        "id": uuid4(),
        "patient_id": uuid4(),
        "drug_code": "AMOX",
        "drug_name": "Amoxicillin",
        "dose": "500mg",
        "route": "oral",
        "start_time": _NOW_ISO,
        "end_time": _NOW_ISO,
    }
    data.update(overrides)
    return data


class TestMedicationEvent:
    """Tests for MedicationEvent model validation."""

    def test_valid_medication(self) -> None:
        """All required fields present with valid values."""
        med = MedicationEvent(**_med_kwargs())
        assert med.drug_code == "AMOX"
        assert med.dose == "500mg"

    def test_uuid_fields_parsed(self) -> None:
        """Both id and patient_id should be UUID objects."""
        med = MedicationEvent(**_med_kwargs())
        assert isinstance(med.id, UUID)
        assert isinstance(med.patient_id, UUID)

    def test_invalid_route_rejected(self) -> None:
        """A route not in the Literal set must be rejected."""
        with pytest.raises(ValidationError):
            MedicationEvent(**_med_kwargs(route="intravenous"))

    def test_route_case_insensitive(self) -> None:
        """Route 'ORAL' should be accepted and normalized to 'oral'."""
        med = MedicationEvent(**_med_kwargs(route="ORAL"))
        assert med.route == "oral"

    def test_empty_drug_code_rejected(self) -> None:
        """drug_code must have min_length=1."""
        with pytest.raises(ValidationError):
            MedicationEvent(**_med_kwargs(drug_code=""))

    def test_datetime_parsed_from_iso(self) -> None:
        """start_time and end_time should accept ISO-8601 strings."""
        med = MedicationEvent(**_med_kwargs())
        assert isinstance(med.start_time, datetime)
        assert isinstance(med.end_time, datetime)

    def test_ingested_at_defaults_to_now(self) -> None:
        """ingested_at should auto-populate when omitted."""
        med = MedicationEvent(**_med_kwargs())
        assert med.ingested_at is not None

    def test_updated_at_defaults_to_now(self) -> None:
        """updated_at should auto-populate when omitted."""
        med = MedicationEvent(**_med_kwargs())
        assert med.updated_at is not None
