"""Add unique constraints to name and url fields

Revision ID: 011632ce78d6
Revises: 3d1a2c00e797
Create Date: 2025-04-24 18:03:54.118308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011632ce78d6'
down_revision: Union[str, None] = '3d1a2c00e797'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('uix_name_url', 'drug_classes_urls', ['name', 'url'])
    op.create_unique_constraint(None, 'drug_classes_urls', ['name'])
    op.create_unique_constraint(None, 'drug_classes_urls', ['url'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'drug_classes_urls', type_='unique')
    op.drop_constraint(None, 'drug_classes_urls', type_='unique')
    op.drop_constraint('uix_name_url', 'drug_classes_urls', type_='unique')
    # ### end Alembic commands ###
