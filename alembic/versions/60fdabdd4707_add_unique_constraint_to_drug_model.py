"""Add unique constraint to Drug model

Revision ID: 60fdabdd4707
Revises: 4946f7590e8f
Create Date: 2025-04-26 10:54:49.344027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60fdabdd4707'
down_revision: Union[str, None] = '4946f7590e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('uix_drug_name_url', 'drugs', ['name', 'url'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uix_drug_name_url', 'drugs', type_='unique')
    # ### end Alembic commands ###
