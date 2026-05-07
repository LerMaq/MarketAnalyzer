"""add new permissions

Revision ID: 2bc4dc9ca004
Revises: 2654d6863502
Create Date: 2026-05-04 23:05:15.867794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bc4dc9ca004'
down_revision: Union[str, None] = '2654d6863502'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Добавляем пермишен task.priority_queue, если его нет
    bind.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description)
            SELECT 'task.priority_queue', 'Приоритетная очередь задач'
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = 'task.priority_queue'
            )
            """
        )
    )

    # 2. Добавляем пермишен worker.manage, если его нет
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

    # 3. Связываем task.priority_queue с рангом premium
    bind.execute(
        sa.text(
            """
            INSERT INTO rank_permissions (rank_id, permission_id)
            SELECT r.id, p.id
            FROM ranks r, permissions p
            WHERE r.name = 'premium'
              AND p.name = 'task.priority_queue'
              AND NOT EXISTS (
                  SELECT 1 FROM rank_permissions rp
                  WHERE rp.rank_id = r.id AND rp.permission_id = p.id
              )
            """
        )
    )

    # 4. Связываем task.priority_queue с рангом admin
    bind.execute(
        sa.text(
            """
            INSERT INTO rank_permissions (rank_id, permission_id)
            SELECT r.id, p.id
            FROM ranks r, permissions p
            WHERE r.name = 'admin'
              AND p.name = 'task.priority_queue'
              AND NOT EXISTS (
                  SELECT 1 FROM rank_permissions rp
                  WHERE rp.rank_id = r.id AND rp.permission_id = p.id
              )
            """
        )
    )

    # 5. Связываем worker.manage с рангом moderator
    bind.execute(
        sa.text(
            """
            INSERT INTO rank_permissions (rank_id, permission_id)
            SELECT r.id, p.id
            FROM ranks r, permissions p
            WHERE r.name = 'moderator'
              AND p.name = 'worker.manage'
              AND NOT EXISTS (
                  SELECT 1 FROM rank_permissions rp
                  WHERE rp.rank_id = r.id AND rp.permission_id = p.id
              )
            """
        )
    )

    # 6. Связываем worker.manage с рангом admin
    bind.execute(
        sa.text(
            """
            INSERT INTO rank_permissions (rank_id, permission_id)
            SELECT r.id, p.id
            FROM ranks r, permissions p
            WHERE r.name = 'admin'
              AND p.name = 'worker.manage'
              AND NOT EXISTS (
                  SELECT 1 FROM rank_permissions rp
                  WHERE rp.rank_id = r.id AND rp.permission_id = p.id
              )
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Удаляем связи task.priority_queue
    bind.execute(
        sa.text(
            """
            DELETE FROM rank_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE name = 'task.priority_queue'
            )
            """
        )
    )

    # Удаляем связи worker.manage
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

    # Удаляем сами пермишены
    bind.execute(
        sa.text("DELETE FROM permissions WHERE name IN ('task.priority_queue', 'worker.manage')")
    )
