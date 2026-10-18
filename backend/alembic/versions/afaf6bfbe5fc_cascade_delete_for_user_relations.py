"""cascade delete for user relations

Revision ID: afaf6bfbe5fc
Revises: 3f0b0244514f
Create Date: 2026-10-18 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'afaf6bfbe5fc'
down_revision: Union[str, Sequence[str], None] = '3f0b0244514f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (constraint name, child table, child column, parent table)
FOREIGN_KEYS = (
    ('events_users_user_id_fkey', 'events_users', 'user_id', 'users'),
    ('expenses_payer_id_fkey', 'expenses', 'payer_id', 'users'),
    ('debts_debtor_id_fkey', 'debts', 'debtor_id', 'users'),
    ('debts_expense_id_fkey', 'debts', 'expense_id', 'expenses'),
)


def upgrade() -> None:
    """Add ON DELETE CASCADE to every foreign key pointing at users (and debts -> expenses)."""
    for name, table, column, parent in FOREIGN_KEYS:
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(name, table, parent, [column], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Restore ON DELETE NO ACTION."""
    for name, table, column, parent in FOREIGN_KEYS:
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(name, table, parent, [column], ['id'])
