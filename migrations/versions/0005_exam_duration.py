"""Add configurable duration to practice and mock exams."""

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("practice_exams", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.add_column("mock_exams", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE practice_exams
        SET duration_minutes = CASE target_group
          WHEN 'doc-hieu' THEN 25
          WHEN 'viet-doan' THEN 35
          WHEN 'viet-bai' THEN 60
          ELSE 45
        END
        """
    )
    op.execute("UPDATE mock_exams SET duration_minutes = 120")
    op.alter_column("practice_exams", "duration_minutes", nullable=False, server_default="45")
    op.alter_column("mock_exams", "duration_minutes", nullable=False, server_default="120")
    op.create_check_constraint(
        "ck_practice_exams_duration_minutes", "practice_exams", "duration_minutes BETWEEN 1 AND 1440"
    )
    op.create_check_constraint(
        "ck_mock_exams_duration_minutes", "mock_exams", "duration_minutes BETWEEN 1 AND 1440"
    )


def downgrade():
    op.drop_constraint("ck_mock_exams_duration_minutes", "mock_exams", type_="check")
    op.drop_constraint("ck_practice_exams_duration_minutes", "practice_exams", type_="check")
    op.drop_column("mock_exams", "duration_minutes")
    op.drop_column("practice_exams", "duration_minutes")
