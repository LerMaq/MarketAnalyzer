"""add_pgvector_extension_and_embedding

Revision ID: 6b7c99277281
Revises: 2bc4dc9ca004
Create Date: 2026-05-11 02:58:57.884356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '6b7c99277281'
down_revision: Union[str, None] = '2bc4dc9ca004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем расширение pgvector
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Добавляем векторное поле в таблицу metrics
    op.add_column('metrics', sa.Column('embedding', Vector(4096), nullable=True))


def downgrade() -> None:
    # Удаляем векторное поле
    op.drop_column('metrics', 'embedding')

    # Удаляем расширение pgvector (осторожно, если используется в других таблицах)
    op.execute('DROP EXTENSION IF EXISTS vector')
