"""Add AI settings, exam rubrics, grading jobs/results and feedback fields."""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("submissions", sa.Column("teacher_improvement_note", sa.Text(), nullable=True))
    op.add_column("submissions", sa.Column("feedback_published", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("submissions", sa.Column("feedback_published_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(150), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("api_key_encrypted", sa.String(1024), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("teacher_id", name="uq_ai_settings_teacher_id"),
    )
    op.create_index("ix_ai_settings_teacher_id", "ai_settings", ["teacher_id"])

    op.create_table(
        "exam_rubrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exam_type", sa.String(20), nullable=False),
        sa.Column("practice_exam_id", sa.Integer(), sa.ForeignKey("practice_exams.id", ondelete="CASCADE"), nullable=True),
        sa.Column("mock_exam_id", sa.Integer(), sa.ForeignKey("mock_exams.id", ondelete="CASCADE"), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("storage_path", sa.String(1000), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("((practice_exam_id IS NOT NULL AND mock_exam_id IS NULL) OR (practice_exam_id IS NULL AND mock_exam_id IS NOT NULL))", name="ck_exam_rubrics_one_exam"),
        sa.CheckConstraint("exam_type IN ('Practice', 'Mock')", name="ck_exam_rubrics_exam_type"),
        sa.CheckConstraint("version >= 1", name="ck_exam_rubrics_version_positive"),
    )
    op.create_index("ix_exam_rubrics_teacher_id", "exam_rubrics", ["teacher_id"])
    op.create_index("ix_exam_rubrics_practice_exam_id", "exam_rubrics", ["practice_exam_id"])
    op.create_index("ix_exam_rubrics_mock_exam_id", "exam_rubrics", ["mock_exam_id"])

    op.create_table(
        "ai_grading_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rubric_id", sa.Integer(), sa.ForeignKey("exam_rubrics.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(150), nullable=False),
        sa.Column("rubric_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="ck_ai_grading_jobs_status"),
    )
    op.create_index("ix_ai_grading_jobs_submission_id", "ai_grading_jobs", ["submission_id"])

    op.create_table(
        "ai_grading_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("ai_grading_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column("overall_comment", sa.Text(), nullable=True),
        sa.Column("improvement_suggestion", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", name="uq_ai_grading_results_job_id"),
    )
    op.create_index("ix_ai_grading_results_submission_id", "ai_grading_results", ["submission_id"])

    op.create_table(
        "ai_grading_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("ai_grading_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("practice_question_id", sa.Integer(), sa.ForeignKey("practice_questions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("mock_question_id", sa.Integer(), sa.ForeignKey("mock_questions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ai_score", sa.Float(), nullable=False),
        sa.Column("ai_question_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("((practice_question_id IS NOT NULL AND mock_question_id IS NULL) OR (practice_question_id IS NULL AND mock_question_id IS NOT NULL))", name="ck_ai_grading_answers_one_question"),
        sa.CheckConstraint("ai_score >= 0", name="ck_ai_grading_answers_score_nonnegative"),
        sa.Index("ix_ai_grading_answers_result_id", "result_id"),
    )


def downgrade():
    op.drop_table("ai_grading_answers")
    op.drop_index("ix_ai_grading_results_submission_id", table_name="ai_grading_results")
    op.drop_table("ai_grading_results")
    op.drop_index("ix_ai_grading_jobs_submission_id", table_name="ai_grading_jobs")
    op.drop_table("ai_grading_jobs")
    op.drop_index("ix_exam_rubrics_mock_exam_id", table_name="exam_rubrics")
    op.drop_index("ix_exam_rubrics_practice_exam_id", table_name="exam_rubrics")
    op.drop_index("ix_exam_rubrics_teacher_id", table_name="exam_rubrics")
    op.drop_table("exam_rubrics")
    op.drop_index("ix_ai_settings_teacher_id", table_name="ai_settings")
    op.drop_table("ai_settings")
    op.drop_column("submissions", "feedback_published_at")
    op.drop_column("submissions", "feedback_published")
    op.drop_column("submissions", "teacher_improvement_note")
