"""extend_eligibility_rules_phase5

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-02

Adds to eligibility_rules table:
  - minimum_income
  - education
  - district
  - require_farmer
  - require_disabled
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "eligibility_rules",
        sa.Column("minimum_income", sa.Integer(), nullable=True,
                  comment="Minimum annual income in INR"),
    )
    op.add_column(
        "eligibility_rules",
        sa.Column("education", sa.Enum(name="education_enum"), nullable=True),
    )
    op.add_column(
        "eligibility_rules",
        sa.Column("district", sa.String(100), nullable=True),
    )
    op.add_column(
        "eligibility_rules",
        sa.Column("require_farmer", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "eligibility_rules",
        sa.Column("require_disabled", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    for col in ["require_disabled", "require_farmer", "district", "education", "minimum_income"]:
        op.drop_column("eligibility_rules", col)
