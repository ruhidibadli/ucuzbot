"""Add email and password_hash to users, make telegram_id nullable

Revision ID: 003
Revises: 002
Create Date: 2025-01-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make telegram_id nullable (was NOT NULL)
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )

    # Add email column (unique, indexed, nullable)
    op.add_column(
        "users",
        sa.Column("email", sa.String(255), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # Add password_hash column (nullable)
    op.add_column(
        "users",
        sa.Column("password_hash", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "password_hash")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_column("users", "email")
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
