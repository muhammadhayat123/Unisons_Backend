"""add designation to users

Revision ID: a1b2c3d4e5f6
Revises: 85938edf281b
Create Date: 2026-09-21 14:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "85938edf281b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# PostgreSQL native enum type name (must match the name= kwarg in the model)
_ENUM_NAME = "designation_enum"
_ENUM_VALUES = ("admin", "seller")


def upgrade() -> None:
    """Add designation_enum type and designation column to users."""
    # 1. Create the native PostgreSQL ENUM type first
    designation_enum = sa.Enum(*_ENUM_VALUES, name=_ENUM_NAME)
    designation_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add the column as nullable so existing rows are not rejected
    op.add_column(
        "users",
        sa.Column(
            "designation",
            sa.Enum(*_ENUM_VALUES, name=_ENUM_NAME),
            nullable=True,
        ),
    )

    # 3. Back-fill existing rows with the default value 'seller'
    op.execute("UPDATE users SET designation = 'seller' WHERE designation IS NULL")

    # 4. Now tighten the constraint to NOT NULL
    op.alter_column("users", "designation", nullable=False)


def downgrade() -> None:
    """Remove designation column and designation_enum type from users."""
    op.drop_column("users", "designation")

    # Drop the native enum type only after the column is gone
    designation_enum = sa.Enum(*_ENUM_VALUES, name=_ENUM_NAME)
    designation_enum.drop(op.get_bind(), checkfirst=True)
