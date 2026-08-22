"""add_user_role_and_last_login

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-31

Adds to users table:
  - role        : user_role_enum (user | admin | super_admin), default 'user'
  - last_login_at : timestamptz nullable
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new enum type
    user_role_enum = postgresql.ENUM(
        "user", "admin", "super_admin",
        name="user_role_enum",
        create_type=False,
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Add role column with default
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum(name="user_role_enum"),
            nullable=False,
            server_default="user",
        ),
    )

    # Add last_login_at audit column
    op.add_column(
        "users",
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Index for admin queries
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "role")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
