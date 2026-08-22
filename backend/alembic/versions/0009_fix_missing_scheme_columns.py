"""add_required_documents_and_application_process_to_schemes

Revision ID: 0009_fix_missing_scheme_columns
Revises: bb75bb4fe3f3
Create Date: 2026-08-11

Root cause fix: The Scheme ORM model defines `required_documents` and
`application_process` columns, but migration 0003 (extend_scheme_model)
never added them to the PostgreSQL table.

This caused ALL public scheme endpoints to return HTTP 500 because
SQLAlchemy tried to SELECT these columns from the DB, which rejected
the query with:
  asyncpg.exceptions.UndefinedColumnError: column schemes.required_documents does not exist

Fix: Add both missing TEXT columns (nullable) to the schemes table.
No data loss — purely additive DDL.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0009_fix_missing_scheme_columns"
down_revision: Union[str, None] = "bb75bb4fe3f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add required_documents (nullable TEXT)
    op.add_column(
        "schemes",
        sa.Column(
            "required_documents",
            sa.Text,
            nullable=True,
            comment="List of documents required for application",
        ),
    )

    # Add application_process (nullable TEXT)
    op.add_column(
        "schemes",
        sa.Column(
            "application_process",
            sa.Text,
            nullable=True,
            comment="Step-by-step application process",
        ),
    )


def downgrade() -> None:
    op.drop_column("schemes", "application_process")
    op.drop_column("schemes", "required_documents")
