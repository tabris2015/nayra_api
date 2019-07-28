"""nueva tabla word

Revision ID: ab5faca97ade
Revises: fd551a7629c6
Create Date: 2019-02-15 15:57:27.593922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab5faca97ade'
down_revision = 'fd551a7629c6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('word',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('word', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_word_word'), 'word', ['word'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_word_word'), table_name='word')
    op.drop_table('word')
    # ### end Alembic commands ###