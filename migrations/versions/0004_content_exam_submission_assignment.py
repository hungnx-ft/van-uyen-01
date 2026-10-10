"""Complete content, exam, submission and assignment storage for the API contract."""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    # These fields are nullable/defaulted so databases created by the legacy HTML
    # backend can be upgraded without inventing content for existing records.
    for table in ("practice_exams", "mock_exams"):
        op.add_column(table, sa.Column("target_group", sa.String(50), nullable=True))
        op.add_column(table, sa.Column("passage", sa.Text(), nullable=False, server_default=""))
        op.add_column(table, sa.Column("genre", sa.String(50), nullable=True))
        op.add_column(table, sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()))
        op.create_index(f"ix_{table}_target_group", table, ["target_group"])

    for table in ("practice_questions", "mock_questions"):
        op.add_column(table, sa.Column("answer_key", sa.Text(), nullable=False, server_default=""))
        op.create_check_constraint(
            f"ck_{table}_max_score_nonnegative", table, "max_score >= 0"
        )
    # Legacy rows had no section validation; retain the row while normalizing
    # unexpected values to the reading section before adding the constraint.
    op.execute("UPDATE mock_questions SET section = 1 WHERE section NOT IN (1, 2)")
    op.create_check_constraint("ck_mock_questions_section", "mock_questions", "section IN (1, 2)")

    op.add_column("theory_articles", sa.Column("main_category", sa.String(50), nullable=True))
    op.add_column("theory_articles", sa.Column("sub_category", sa.String(80), nullable=True))
    op.add_column("theory_articles", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    op.add_column("theory_articles", sa.Column("icon", sa.String(20), nullable=False, server_default="📚"))
    op.add_column("theory_articles", sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_theory_articles_main_category", "theory_articles", ["main_category"])
    op.create_index("ix_theory_articles_sub_category", "theory_articles", ["sub_category"])

    op.add_column("submissions", sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("submissions", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("submissions", sa.Column("self_score", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("teacher_score", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("teacher_comment", sa.Text(), nullable=True))
    op.create_check_constraint("ck_submissions_attempt_positive", "submissions", "attempt >= 1")
    op.create_check_constraint("ck_submissions_leave_tab_nonnegative", "submissions", "leave_tab_count >= 0")
    op.create_check_constraint("ck_submissions_self_score_nonnegative", "submissions", "self_score IS NULL OR self_score >= 0")
    op.create_check_constraint("ck_submissions_teacher_score_nonnegative", "submissions", "teacher_score IS NULL OR teacher_score >= 0")
    # Older grading code could create a second score for an answer. Keep the
    # first score before enforcing the one-score-per-answer contract.
    op.execute("""
        DELETE FROM submission_scores older
        USING submission_scores newer
        WHERE older.answer_id = newer.answer_id AND older.id > newer.id
    """)
    op.create_unique_constraint("uq_submission_scores_answer_id", "submission_scores", ["answer_id"])
    op.create_check_constraint("ck_submission_scores_nonnegative", "submission_scores", "score >= 0")

    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("exam_type", sa.String(20), nullable=False),
        sa.Column("practice_exam_id", sa.Integer(), sa.ForeignKey("practice_exams.id"), nullable=True),
        sa.Column("mock_exam_id", sa.Integer(), sa.ForeignKey("mock_exams.id"), nullable=True),
        sa.Column("exam_title", sa.String(300), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("class_id", "exam_type", "practice_exam_id", "mock_exam_id", name="uq_assignments_class_exam"),
    )
    op.create_index("ix_assignments_id", "assignments", ["id"])
    op.create_index("ix_assignments_teacher_id", "assignments", ["teacher_id"])
    op.create_index("ix_assignments_class_id", "assignments", ["class_id"])


def downgrade():
    op.drop_index("ix_assignments_class_id", table_name="assignments")
    op.drop_index("ix_assignments_teacher_id", table_name="assignments")
    op.drop_index("ix_assignments_id", table_name="assignments")
    op.drop_table("assignments")

    op.drop_constraint("ck_submission_scores_nonnegative", "submission_scores", type_="check")
    op.drop_constraint("uq_submission_scores_answer_id", "submission_scores", type_="unique")
    for name in ("ck_submissions_teacher_score_nonnegative", "ck_submissions_self_score_nonnegative", "ck_submissions_leave_tab_nonnegative", "ck_submissions_attempt_positive"):
        op.drop_constraint(name, "submissions", type_="check")
    for column in ("teacher_comment", "teacher_score", "self_score", "submitted_at", "attempt"):
        op.drop_column("submissions", column)

    for index in ("ix_theory_articles_sub_category", "ix_theory_articles_main_category"):
        op.drop_index(index, table_name="theory_articles")
    for column in ("is_published", "icon", "description", "sub_category", "main_category"):
        op.drop_column("theory_articles", column)

    op.drop_constraint("ck_mock_questions_section", "mock_questions", type_="check")
    for table in ("practice_questions", "mock_questions"):
        op.drop_constraint(f"ck_{table}_max_score_nonnegative", table, type_="check")
        op.drop_column(table, "answer_key")
    for table in ("practice_exams", "mock_exams"):
        op.drop_index(f"ix_{table}_target_group", table_name=table)
        for column in ("is_published", "genre", "passage", "target_group"):
            op.drop_column(table, column)
