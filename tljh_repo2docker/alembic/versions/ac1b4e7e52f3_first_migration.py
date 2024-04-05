"""First migration

Revision ID: ac1b4e7e52f3
Revises:
Create Date: 2024-04-05 16:25:18.246631

"""

# revision identifiers, used by Alembic.
revision = "ac1b4e7e52f3"
down_revision = None
branch_labels = None
depends_on = None

import sqlalchemy as sa  # noqa
from alembic import op  # noqa
from jupyterhub.orm import JSONDict  # noqa


def upgrade():
    op.create_table(
        "images",
        sa.Column("uid", sa.Unicode(36)),
        sa.Column("name", sa.Unicode(4096)),
        sa.Column("metadata", JSONDict, nullable=True),
    )


def downgrade():
    op.drop_table("images")
