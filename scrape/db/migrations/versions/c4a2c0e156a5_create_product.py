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


def create_products_table() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("price", sa.Float, nullable=True),
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


def upgrade() -> None:
    """Upgrade schema."""
    create_updated_at_trigger()
    create_products_table()


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_products_url", table_name="products")
    op.drop_table("products")
