"""Add discourse_topics table and users.username column

Revision ID: 4309a04aaea9
Revises: 41c4d0ca1619
Create Date: 2016-03-03 16:25:34.715094

"""

# revision identifiers, used by Alembic.
revision = '4309a04aaea9'
down_revision = '41c4d0ca1619'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('discourse_topics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('discourse_id', sa.Integer(), nullable=True),
    sa.Column('slug', sa.Text(), nullable=True),
    sa.Column('excerpt', sa.Text(), nullable=True),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('posts_count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['user_events.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('discourse_id')
    )
    op.add_column(u'users', sa.Column('username', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column(u'users', 'username')
    op.drop_table('discourse_topics')
    ### end Alembic commands ###