"""Add new enum values

Revision ID: 24482872464d
Revises: 797fd7422c34
Create Date: 2026-08-07 12:03:46.894963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24482872464d'
down_revision: Union[str, None] = '797fd7422c34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to translation_status_enum
    op.execute("ALTER TYPE translation_status_enum ADD VALUE IF NOT EXISTS 'pending_review'")
    op.execute("ALTER TYPE translation_status_enum ADD VALUE IF NOT EXISTS 'approved'")
    op.execute("ALTER TYPE translation_status_enum ADD VALUE IF NOT EXISTS 'published'")
    op.execute("ALTER TYPE translation_status_enum ADD VALUE IF NOT EXISTS 'rejected'")
    
    # Add new values to user_role_enum
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'translation_manager'")
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'editor'")
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'viewer'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing values from an ENUM type easily.
    pass
