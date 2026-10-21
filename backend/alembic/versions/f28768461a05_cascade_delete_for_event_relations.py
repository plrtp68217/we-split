"""cascade delete for event relations

Revision ID: f28768461a05
Revises: afaf6bfbe5fc
Create Date: 2026-10-21 15:09:37.662677

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f28768461a05'
down_revision: Union[str, Sequence[str], None] = 'afaf6bfbe5fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (constraint name, child table, child column, parent table)
FOREIGN_KEYS = (
    ('events_users_event_id_fkey', 'events_users', 'event_id', 'events'),
    ('expenses_event_id_fkey', 'expenses', 'event_id', 'events'),
)


def upgrade() -> None:
    """Add ON DELETE CASCADE to every foreign key pointing at events."""
    for name, table, column, parent in FOREIGN_KEYS:
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(name, table, parent, [column], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Restore ON DELETE NO ACTION."""
    for name, table, column, parent in FOREIGN_KEYS:
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(name, table, parent, [column], ['id'])
