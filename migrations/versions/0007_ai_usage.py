"""Track AI token usage and estimated cost."""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ai_grading_jobs", sa.Column("prompt_tokens", sa.Integer(), nullable=True))
    op.add_column("ai_grading_jobs", sa.Column("completion_tokens", sa.Integer(), nullable=True))
    op.add_column("ai_grading_jobs", sa.Column("total_tokens", sa.Integer(), nullable=True))
    op.add_column("ai_grading_jobs", sa.Column("estimated_cost_usd", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("ai_grading_jobs", "estimated_cost_usd")
    op.drop_column("ai_grading_jobs", "total_tokens")
    op.drop_column("ai_grading_jobs", "completion_tokens")
    op.drop_column("ai_grading_jobs", "prompt_tokens")
