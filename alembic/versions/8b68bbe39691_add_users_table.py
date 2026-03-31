"""add users table

Revision ID: 8b68bbe39691
Revises: 30b0a4afe4c8
Create Date: 2026-03-30 17:12:04.550057

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8b68bbe39691"
down_revision: Union[str, Sequence[str], None] = "30b0a4afe4c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("main", sa.Column("user_id_new", sa.Integer(), nullable=True))
    op.execute("""
        UPDATE main
        SET user_id_new = (
            SELECT id FROM users WHERE users.telegram_id = main.user_id
        )
    """)
    op.drop_column("main", "user_id")
    op.alter_column("main", "user_id_new", new_column_name="user_id")
    op.create_foreign_key("fk_main_user", "main", "users", ["user_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    pass
