"""Update Task model

Revision ID: 8e41d44436ce
Revises: 5be1daaa7492
Create Date: 2026-03-15 01:12:19.573444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8e41d44436ce'
down_revision: Union[str, None] = '5be1daaa7492'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Сначала создаем сам тип ENUM в базе данных (Alembic часто это пропускает)
    task_status_enum = postgresql.ENUM('pending', 'fetching', 'processing', 'completed', 'failed', name='taskstatus')
    task_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Добавляем колонки.
    # Для retry_count ты уже добавил server_default='0' — это супер.
    # Для updated_at тоже лучше добавить default, чтобы не было пустых значений в старых записях.
    op.add_column('tasks', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tasks', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))

    # 3. Изменяем тип колонки status.
    # Добавляем postgresql_using, чтобы конвертировать строку в Enum.
    op.alter_column('tasks', 'status',
                    existing_type=sa.VARCHAR(),
                    type_=task_status_enum,
                    existing_nullable=False,
                    postgresql_using="status::taskstatus")  # КРИТИЧЕСКИ ВАЖНО


def downgrade() -> None:
    # Возвращаем тип обратно в VARCHAR
    op.alter_column('tasks', 'status',
                    existing_type=postgresql.ENUM('pending', 'fetching', 'processing', 'completed', 'failed',
                                                  name='taskstatus'),
                    type_=sa.VARCHAR(),
                    existing_nullable=False)

    op.drop_column('tasks', 'updated_at')
    op.drop_column('tasks', 'retry_count')

    # Удаляем тип ENUM из базы
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
