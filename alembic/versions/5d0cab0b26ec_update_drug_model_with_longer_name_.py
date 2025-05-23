"""Update Drug model with longer name field and composite unique constraint

Revision ID: 5d0cab0b26ec
Revises: 60fdabdd4707
Create Date: 2025-04-26 11:05:11.506812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d0cab0b26ec'
down_revision: Union[str, None] = '60fdabdd4707'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('drugs', 'name',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=1024),
               existing_nullable=False)
    op.drop_constraint('drugs_name_key', 'drugs', type_='unique')
    op.drop_constraint('drugs_url_key', 'drugs', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('drugs_url_key', 'drugs', ['url'])
    op.create_unique_constraint('drugs_name_key', 'drugs', ['name'])
    op.alter_column('drugs', 'name',
               existing_type=sa.String(length=1024),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    # ### end Alembic commands ###
