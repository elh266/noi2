"""enforce uniqueness based on discourse_id and post_number

Revision ID: 51bdb7c7928a
Revises: 28ff85fcc188
Create Date: 2016-03-22 22:02:14.557660

"""

# revision identifiers, used by Alembic.
revision = '51bdb7c7928a'
down_revision = '28ff85fcc188'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'discourse_topics_discourse_id_key', 'discourse_topics', type_='unique')
    op.create_unique_constraint(None, 'discourse_topics', ['discourse_id', 'post_number'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'discourse_topics', type_='unique')
    op.create_unique_constraint(u'discourse_topics_discourse_id_key', 'discourse_topics', ['discourse_id'])
    ### end Alembic commands ###