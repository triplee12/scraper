"""create Product

Revision ID: c4a2c0e156a5
Revises: 
Create Date: 2025-10-30 10:24:03.523065

"""
from typing import Sequence, Union, Tuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4a2c0e156a5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
    )


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        *timestamps(indexed=True),
    )

    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.execute(
        """
        CREATE TRIGGER update_users_modtime
            BEFORE UPDATE
            ON users
            FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_retailers_table() -> None:
    op.create_table(
        "retailers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        *timestamps(indexed=True),
    )

    op.create_index("ix_retailers_url", "retailers", ["base_url"], unique=True)

    op.execute(
        """
        CREATE TRIGGER update_retailers_modtime
            BEFORE UPDATE
            ON retailers
            FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_products_table() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("retailer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("retailers.id"), nullable=False),
        *timestamps(indexed=True),
    )

    op.create_index("ix_products_url", "products", ["url"], unique=True)

    op.execute(
        """
        CREATE TRIGGER update_products_modtime
            BEFORE UPDATE
            ON products
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_price_history_table() -> None:
    op.create_table(
        "price_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        *timestamps(indexed=True),
    )

    op.execute(
        """
        CREATE TRIGGER update_price_history_modtime
            BEFORE UPDATE
            ON price_history
            FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_alerts_table() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("target_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_triggered", sa.Boolean, default=False, nullable=False),
        *timestamps(indexed=True),
    )

    op.execute(
        """
        CREATE TRIGGER update_alerts_modtime
            BEFORE UPDATE
            ON alerts
            FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_scrape_tasks_table() -> None:
    op.create_table(
        "scrape_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("status", sa.String(255), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.execute(
        """
        CREATE TRIGGER update_scrape_tasks_modtime
            BEFORE UPDATE
            ON scrape_tasks
            FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def upgrade() -> None:
    """Upgrade schema."""
    create_updated_at_trigger()
    create_users_table()
    create_retailers_table()
    create_products_table()
    create_price_history_table()
    create_alerts_table()
    create_scrape_tasks_table()


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_retailers_url", table_name="retailers")
    op.drop_table("retailers")
    op.drop_index("ix_products_url", table_name="products")
    op.drop_table("products")
    op.drop_table("price_history")
    op.drop_table("alerts")
    op.drop_table("scrape_tasks")
