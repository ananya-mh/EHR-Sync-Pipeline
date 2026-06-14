"""Initial schema with patients, lab_results, and medications tables.

Revision ID: 001
Revises: None
Create Date: 2026-06-14

Matches the existing postgres/init.sql schema with the addition of an
updated_at column on all three tables for timestamp-based upsert logic.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create uuid-ossp extension and all three EHR tables."""
    # Enable UUID generation.
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "patients",
        sa.Column("id", sa.dialects.postgresql.UUID(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("condition", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("age BETWEEN 0 AND 120", name="ck_patients_age_range"),
    )

    op.create_table(
        "lab_results",
        sa.Column("id", sa.dialects.postgresql.UUID(), primary_key=True),
        sa.Column(
            "patient_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("patients.id"),
            nullable=True,
        ),
        sa.Column("test_code", sa.Text(), nullable=True),
        sa.Column("test_name", sa.Text(), nullable=True),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("result_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )

    op.create_table(
        "medications",
        sa.Column("id", sa.dialects.postgresql.UUID(), primary_key=True),
        sa.Column(
            "patient_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("patients.id"),
            nullable=True,
        ),
        sa.Column("drug_code", sa.Text(), nullable=True),
        sa.Column("drug_name", sa.Text(), nullable=True),
        sa.Column("dose", sa.Text(), nullable=True),
        sa.Column("route", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Drop all three EHR tables in reverse dependency order."""
    op.drop_table("medications")
    op.drop_table("lab_results")
    op.drop_table("patients")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
