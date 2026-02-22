"""Add push_subscriptions table and push_subscription_id to alerts

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create push_subscriptions table
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_push_subs_user_id", "push_subscriptions", ["user_id"])
    op.create_index(
        "idx_push_subs_active",
        "push_subscriptions",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # Make alerts.user_id nullable (for push-only alerts)
    op.alter_column("alerts", "user_id", existing_type=sa.Integer(), nullable=True)

    # Add push_subscription_id to alerts
    op.add_column(
        "alerts",
        sa.Column(
            "push_subscription_id",
            sa.Integer(),
            sa.ForeignKey("push_subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("alerts", "push_subscription_id")
    op.alter_column("alerts", "user_id", existing_type=sa.Integer(), nullable=False)
    op.drop_table("push_subscriptions")
