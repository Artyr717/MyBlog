"""Update Post for cascading deletes

Revision ID: 13a2768584bc
Revises: 
Create Date: 2024-09-01 00:32:45.332167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13a2768584bc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.drop_index('ix_comment_post_id')
        batch_op.drop_index('ix_comment_timestamp')
        batch_op.drop_index('ix_comment_user_id')

    op.drop_table('comment')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('content', sa.VARCHAR(length=140), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('post_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.create_index('ix_comment_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_comment_timestamp', ['timestamp'], unique=False)
        batch_op.create_index('ix_comment_post_id', ['post_id'], unique=False)

    # ### end Alembic commands ###