"""Track worker attempts for bounded retries."""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ai_grading_jobs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("ai_grading_jobs", "attempt_count")
