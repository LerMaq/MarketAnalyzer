"""workers entity and review_count

Revision ID: c4f1a9d8e3b2
Revises: b7643b0f866f
Create Date: 2026-05-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f1a9d8e3b2'
down_revision: Union[str, None] = 'b7643b0f866f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Создаём таблицу workers
    op.create_table(
        'workers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('token', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['created_by_user_id'], ['users.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_workers_token'),
    )
    op.create_index('ix_workers_token', 'workers', ['token'], unique=True)

    # 2. Сбрасываем зависшие задачи и старые ссылки worker_id (они вели на users.id,
    #    после смены FK были бы невалидны)
    bind.execute(
        sa.text(
            "UPDATE tasks SET status = 'failed', worker_id = NULL "
            "WHERE status IN ('fetching', 'processing')"
        )
    )
    bind.execute(sa.text("UPDATE tasks SET worker_id = NULL"))

    # 3. Меняем FK у tasks.worker_id с users -> workers
    #    Имя старого constraint авто-сгенерировано, ищем его динамически.
    fk_row = bind.execute(
        sa.text(
            """
            SELECT con.conname
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_attribute att
                 ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
            WHERE rel.relname = 'tasks'
              AND con.contype = 'f'
              AND att.attname = 'worker_id'
            """
        )
    ).fetchone()
    if fk_row:
        op.drop_constraint(fk_row[0], 'tasks', type_='foreignkey')

    op.create_foreign_key(
        'tasks_worker_id_fkey',
        'tasks',
        'workers',
        ['worker_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 4. Добавляем review_count в tasks
    op.add_column(
        'tasks',
        sa.Column(
            'review_count',
            sa.Integer(),
            nullable=False,
            server_default='50',
        ),
    )

    # 5. Чистим устаревшие данные пермишенов/рангов и добавляем worker.manage
    # 5.1 Удаляем UserRank где rank.name='worker'
    bind.execute(
        sa.text(
            """
            DELETE FROM user_ranks
            WHERE rank_id IN (SELECT id FROM ranks WHERE name = 'worker')
            """
        )
    )
    # 5.2 Удаляем RankPermission, ссылающиеся на ранг worker
    bind.execute(
        sa.text(
            """
            DELETE FROM rank_permissions
            WHERE rank_id IN (SELECT id FROM ranks WHERE name = 'worker')
            """
        )
    )
    # 5.3 Удаляем RankPermission, ссылающиеся на пермишен task.worker
    bind.execute(
        sa.text(
            """
            DELETE FROM rank_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE name = 'task.worker'
            )
            """
        )
    )
    # 5.4 Удаляем сам ранг worker
    bind.execute(sa.text("DELETE FROM ranks WHERE name = 'worker'"))
    # 5.5 Удаляем пермишен task.worker
    bind.execute(sa.text("DELETE FROM permissions WHERE name = 'task.worker'"))

    # 5.6 Добавляем пермишен worker.manage и связи с admin/moderator
    bind.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description)
            SELECT 'worker.manage', 'Управление воркерами'
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = 'worker.manage'
            )
            """
        )
    )
    for rank_name in ('admin', 'moderator'):
        bind.execute(
            sa.text(
                """
                INSERT INTO rank_permissions (rank_id, permission_id)
                SELECT r.id, p.id
                FROM ranks r, permissions p
                WHERE r.name = :rank_name
                  AND p.name = 'worker.manage'
                  AND NOT EXISTS (
                      SELECT 1 FROM rank_permissions rp
                      WHERE rp.rank_id = r.id AND rp.permission_id = p.id
                  )
                """
            ),
            {"rank_name": rank_name},
        )


def downgrade() -> None:
    bind = op.get_bind()

    # Откат пермишенов и ранга worker
    bind.execute(
        sa.text(
            """
            DELETE FROM rank_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE name = 'worker.manage'
            )
            """
        )
    )
    bind.execute(sa.text("DELETE FROM permissions WHERE name = 'worker.manage'"))

    # Восстанавливаем пермишен task.worker и ранг worker (с базовыми лимитами)
    bind.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description)
            SELECT 'task.worker', 'Функционал воркера'
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = 'task.worker'
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO ranks (name, level, daily_analysis_limit, daily_chat_limit)
            SELECT 'worker', 30, NULL, 50
            WHERE NOT EXISTS (
                SELECT 1 FROM ranks WHERE name = 'worker'
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO rank_permissions (rank_id, permission_id)
            SELECT r.id, p.id FROM ranks r, permissions p
            WHERE r.name = 'worker' AND p.name IN ('task.worker', 'chat.ask')
              AND NOT EXISTS (
                  SELECT 1 FROM rank_permissions rp
                  WHERE rp.rank_id = r.id AND rp.permission_id = p.id
              )
            """
        )
    )

    # Удаляем review_count
    op.drop_column('tasks', 'review_count')

    # Возвращаем FK tasks.worker_id -> users.id
    bind.execute(sa.text("UPDATE tasks SET worker_id = NULL"))
    op.drop_constraint('tasks_worker_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key(
        'tasks_worker_id_fkey', 'tasks', 'users', ['worker_id'], ['id']
    )

    # Удаляем таблицу workers
    op.drop_index('ix_workers_token', table_name='workers')
    op.drop_table('workers')
