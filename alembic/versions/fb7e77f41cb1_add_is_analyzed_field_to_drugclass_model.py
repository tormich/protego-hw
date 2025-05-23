"""Add is_analyzed field to DrugClass model

Revision ID: fb7e77f41cb1
Revises: 5d7b34c10ec1
Create Date: 2025-04-25 00:22:08.493221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fb7e77f41cb1'
down_revision: Union[str, None] = '5d7b34c10ec1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drug_classes_urls', sa.Column('is_analyzed', sa.Boolean(), nullable=True))
    op.alter_column('drugs', 'ndc_codes',
               existing_type=postgresql.ARRAY(sa.VARCHAR(length=13)),
               type_=sa.ARRAY(sa.String(length=100)),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('drugs', 'ndc_codes',
               existing_type=sa.ARRAY(sa.String(length=100)),
               type_=postgresql.ARRAY(sa.VARCHAR(length=13)),
               existing_nullable=True)
    op.drop_column('drug_classes_urls', 'is_analyzed')
    # ### end Alembic commands ###
