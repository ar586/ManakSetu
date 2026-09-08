"""add source text and ai summary fields

Revision ID: 7e2d1a0f4c3b
Revises: 51a00696d541
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7e2d1a0f4c3b"
down_revision: Union[str, Sequence[str], None] = "51a00696d541"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("standards", sa.Column("source_text", sa.Text(), nullable=True))
    op.add_column("standards", sa.Column("ai_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("standards", "ai_summary")
    op.drop_column("standards", "source_text")