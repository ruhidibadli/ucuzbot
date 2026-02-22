"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("language_code", sa.String(10), server_default="az"),
        sa.Column("subscription_tier", sa.String(20), server_default="free"),
        sa.Column("max_alerts", sa.Integer(), server_default="5"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("search_url_template", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("scraper_class", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_query", sa.String(500), nullable=False),
        sa.Column("target_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("store_slugs", sa.ARRAY(sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_triggered", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lowest_price_found", sa.Numeric(10, 2), nullable=True),
        sa.Column("lowest_price_store", sa.String(50), nullable=True),
        sa.Column("lowest_price_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_alerts_user_id", "alerts", ["user_id"])
    op.create_index(
        "idx_alerts_active", "alerts", ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "price_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_slug", sa.String(50), nullable=False),
        sa.Column("product_name", sa.String(1000), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("product_url", sa.Text(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_price_records_alert_id", "price_records", ["alert_id"])
    op.create_index("idx_price_records_scraped_at", "price_records", ["scraped_at"])


def downgrade() -> None:
    op.drop_table("price_records")
    op.drop_table("alerts")
    op.drop_table("stores")
    op.drop_table("users")
