"""extend_scheme_model_phase4

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-02

Extends the schemes table with Phase 4 production fields:
  - scheme_code (unique, NOT NULL)
  - short_description, full_description (replaces description)
  - scheme_type, application_mode (new enums)
  - ministry, department, district
  - application_start_date, application_end_date
  - official_pdf_url, contact_email, contact_phone
  - is_featured, view_count
  - created_by, updated_by (UUID audit)

Also extends scheme_category_enum with new values.
Creates scheme_type_enum and application_mode_enum.
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New ENUM types ────────────────────────────────────────────────────
    scheme_type_enum = postgresql.ENUM(
        "central", "state",
        name="scheme_type_enum", create_type=False,
    )
    scheme_type_enum.create(op.get_bind(), checkfirst=True)

    application_mode_enum = postgresql.ENUM(
        "online", "offline", "both",
        name="application_mode_enum", create_type=False,
    )
    application_mode_enum.create(op.get_bind(), checkfirst=True)

    # Add new enum values to existing scheme_category_enum
    # PostgreSQL ALTER TYPE ADD VALUE is transactional in PG 12+
    new_category_values = [
        "farmer", "student", "women", "healthcare",
        "business", "tribal", "transport", "finance",
    ]
    conn = op.get_bind()
    for val in new_category_values:
        conn.execute(
            sa.text(
                f"ALTER TYPE scheme_category_enum ADD VALUE IF NOT EXISTS '{val}'"
            )
        )

    # ── Add new columns to schemes ────────────────────────────────────────
    op.add_column(
        "schemes",
        sa.Column("scheme_code", sa.String(50), nullable=True),  # nullable first, fill, then NOT NULL
    )
    # Give existing rows a placeholder code before adding NOT NULL
    op.execute(
        sa.text(
            "UPDATE schemes SET scheme_code = 'CODE-' || SUBSTRING(id::text, 1, 8) "
            "WHERE scheme_code IS NULL"
        )
    )
    op.alter_column("schemes", "scheme_code", nullable=False)
    op.create_unique_constraint("uq_schemes_scheme_code", "schemes", ["scheme_code"])
    op.create_index("ix_schemes_scheme_code", "schemes", ["scheme_code"], unique=True)

    op.add_column("schemes", sa.Column("short_description", sa.String(500), nullable=True))
    op.add_column("schemes", sa.Column("full_description", sa.Text, nullable=True))

    # Migrate existing description → full_description
    op.execute(
        sa.text(
            "UPDATE schemes SET full_description = description WHERE description IS NOT NULL"
        )
    )

    op.add_column(
        "schemes",
        sa.Column(
            "scheme_type",
            sa.Enum(name="scheme_type_enum"),
            nullable=False,
            server_default="central",
        ),
    )
    op.add_column("schemes", sa.Column("ministry", sa.String(300), nullable=True))
    op.add_column("schemes", sa.Column("department", sa.String(300), nullable=True))
    op.add_column("schemes", sa.Column("district", sa.String(100), nullable=True))
    op.add_column(
        "schemes",
        sa.Column(
            "application_mode",
            sa.Enum(name="application_mode_enum"),
            nullable=False,
            server_default="online",
        ),
    )
    op.add_column("schemes", sa.Column("application_start_date", sa.Date, nullable=True))
    op.add_column("schemes", sa.Column("application_end_date", sa.Date, nullable=True))
    op.add_column("schemes", sa.Column("official_pdf_url", sa.String(2000), nullable=True))
    op.add_column("schemes", sa.Column("contact_email", sa.String(255), nullable=True))
    op.add_column("schemes", sa.Column("contact_phone", sa.String(20), nullable=True))
    op.add_column(
        "schemes",
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "schemes",
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "schemes",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "schemes",
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Drop old description column (data preserved in full_description)
    op.drop_column("schemes", "description")

    # Drop old name-state index, replace with unique constraint
    op.drop_index("ix_schemes_name_state", table_name="schemes")
    op.create_unique_constraint("uq_schemes_name_state", "schemes", ["name", "state"])

    # New indexes
    op.create_index("ix_schemes_type_category", "schemes", ["scheme_type", "category"])
    op.create_index("ix_schemes_is_active_featured", "schemes", ["is_active", "is_featured"])
    op.create_index("ix_schemes_ministry", "schemes", ["ministry"])
    op.create_index("ix_schemes_application_mode", "schemes", ["application_mode"])
    op.create_index("ix_schemes_dates", "schemes", ["application_start_date", "application_end_date"])


def downgrade() -> None:
    # Reverse index/constraint changes
    op.drop_index("ix_schemes_dates", table_name="schemes")
    op.drop_index("ix_schemes_application_mode", table_name="schemes")
    op.drop_index("ix_schemes_ministry", table_name="schemes")
    op.drop_index("ix_schemes_is_active_featured", table_name="schemes")
    op.drop_index("ix_schemes_type_category", table_name="schemes")
    op.drop_constraint("uq_schemes_name_state", "schemes", type_="unique")
    op.create_index("ix_schemes_name_state", "schemes", ["name", "state"])

    # Restore description column
    op.add_column("schemes", sa.Column("description", sa.Text, nullable=True))
    op.execute(sa.text("UPDATE schemes SET description = full_description"))

    # Drop new columns
    for col in [
        "updated_by", "created_by", "view_count", "is_featured",
        "contact_phone", "contact_email", "official_pdf_url",
        "application_end_date", "application_start_date",
        "application_mode", "district", "department", "ministry",
        "scheme_type", "full_description", "short_description",
    ]:
        op.drop_column("schemes", col)

    op.drop_index("ix_schemes_scheme_code", table_name="schemes")
    op.drop_constraint("uq_schemes_scheme_code", "schemes", type_="unique")
    op.drop_column("schemes", "scheme_code")

    op.execute(sa.text("DROP TYPE IF EXISTS application_mode_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS scheme_type_enum"))
