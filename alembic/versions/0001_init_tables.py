"""init tables
Revision ID: 0001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass  # Tables are created via SQLModel.metadata.create_all on startup


def downgrade():
    pass
