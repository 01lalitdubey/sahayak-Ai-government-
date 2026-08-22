"""initial_schema_all_tables

Revision ID: 0001
Revises: 
Create Date: 2026-07-30

Creates all Phase 1 tables:
  - users
  - profiles
  - schemes
  - eligibility_rules
  - chat_history

And all PostgreSQL ENUM types used by those tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ENUM types ────────────────────────────────────────────────────────
    gender_enum = postgresql.ENUM(
        "male", "female", "other", "prefer_not_to_say",
        name="gender_enum", create_type=False,
    )
    gender_enum.create(op.get_bind(), checkfirst=True)

    occupation_enum = postgresql.ENUM(
        "farmer", "agricultural_labourer", "self_employed", "salaried",
        "daily_wage", "unemployed", "student", "homemaker", "retired", "other",
        name="occupation_enum", create_type=False,
    )
    occupation_enum.create(op.get_bind(), checkfirst=True)

    education_enum = postgresql.ENUM(
        "no_formal_education", "primary", "middle", "secondary",
        "higher_secondary", "graduate", "post_graduate", "doctorate", "other",
        name="education_enum", create_type=False,
    )
    education_enum.create(op.get_bind(), checkfirst=True)

    category_enum = postgresql.ENUM(
        "general", "obc", "sc", "st", "ews", "other",
        name="category_enum", create_type=False,
    )
    category_enum.create(op.get_bind(), checkfirst=True)

    scheme_category_enum = postgresql.ENUM(
        "agriculture", "education", "health", "housing", "women_and_child",
        "social_welfare", "financial_inclusion", "skill_development",
        "rural_development", "pension", "insurance", "employment",
        "disability", "minority", "other",
        name="scheme_category_enum", create_type=False,
    )
    scheme_category_enum.create(op.get_bind(), checkfirst=True)

    language_enum = postgresql.ENUM(
        "en", "hi", "ta", "te", "bn", "mr", "gu", "kn",
        "ml", "pa", "or", "as", "ur",
        name="language_enum", create_type=False,
    )
    language_enum.create(op.get_bind(), checkfirst=True)

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_email_is_active", "users", ["email", "is_active"])

    # ── profiles ───────────────────────────────────────────────────────────
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", postgresql.ENUM(name="gender_enum", create_type=False), nullable=True),
        sa.Column("occupation", postgresql.ENUM(name="occupation_enum", create_type=False), nullable=True),
        sa.Column("annual_income", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("education", postgresql.ENUM(name="education_enum", create_type=False), nullable=True),
        sa.Column("category", postgresql.ENUM(name="category_enum", create_type=False), nullable=True),
        sa.Column("is_farmer", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_disabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])
    op.create_index("ix_profiles_state_category", "profiles", ["state", "category"])
    op.create_index("ix_profiles_income_category", "profiles", ["annual_income", "category"])

    # ── schemes ────────────────────────────────────────────────────────────
    op.create_table(
        "schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("category", postgresql.ENUM(name="scheme_category_enum", create_type=False), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("official_url", sa.String(1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_schemes_name", "schemes", ["name"])
    op.create_index("ix_schemes_category", "schemes", ["category"])
    op.create_index("ix_schemes_state", "schemes", ["state"])
    op.create_index("ix_schemes_is_active", "schemes", ["is_active"])
    op.create_index("ix_schemes_category_state", "schemes", ["category", "state"])
    op.create_index("ix_schemes_name_state", "schemes", ["name", "state"])

    # ── eligibility_rules ─────────────────────────────────────────────────
    op.create_table(
        "eligibility_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("minimum_age", sa.Integer(), nullable=True),
        sa.Column("maximum_age", sa.Integer(), nullable=True),
        sa.Column("maximum_income", sa.Integer(), nullable=True),
        sa.Column("gender", postgresql.ENUM(name="gender_enum", create_type=False), nullable=True),
        sa.Column("occupation", postgresql.ENUM(name="occupation_enum", create_type=False), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("category", postgresql.ENUM(name="category_enum", create_type=False), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["scheme_id"], ["schemes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eligibility_rules_scheme_id", "eligibility_rules", ["scheme_id"])
    op.create_index(
        "ix_eligibility_rules_state_category",
        "eligibility_rules",
        ["state", "category"],
    )

    # ── chat_history ──────────────────────────────────────────────────────
    op.create_table(
        "chat_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "language",
            postgresql.ENUM(name="language_enum", create_type=False),
            server_default="en",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_history_user_id", "chat_history", ["user_id"])
    op.create_index(
        "ix_chat_history_user_created",
        "chat_history",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("chat_history")
    op.drop_table("eligibility_rules")
    op.drop_table("schemes")
    op.drop_table("profiles")
    op.drop_table("users")

    # Drop ENUMs
    for enum_name in [
        "language_enum", "scheme_category_enum", "category_enum",
        "education_enum", "occupation_enum", "gender_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
