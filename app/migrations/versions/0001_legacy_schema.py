"""Baseline matching the pre-migration backend schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def primary_key():
    return sa.Column("id", sa.Integer(), primary_key=True)


def timestamp():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))


def upgrade():
    op.create_table("users", primary_key(), sa.Column("username", sa.String(), nullable=False),
                    sa.Column("password_hash", sa.String(), nullable=False),
                    sa.Column("role", sa.String(), nullable=False), sa.Column("class_id", sa.Integer()), timestamp())
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("classes", primary_key(), sa.Column("name", sa.String(), nullable=False),
                    sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), timestamp())
    op.create_index("ix_classes_id", "classes", ["id"])
    op.create_index("ix_classes_name", "classes", ["name"])
    op.create_foreign_key("users_class_id_fkey", "users", "classes", ["class_id"], ["id"])
    op.create_table("theory_articles", primary_key(), sa.Column("title", sa.String(), nullable=False),
                    sa.Column("content_type", sa.String(), nullable=False), sa.Column("content", sa.Text(), nullable=False),
                    sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), timestamp())
    op.create_index("ix_theory_articles_id", "theory_articles", ["id"])
    op.create_index("ix_theory_articles_title", "theory_articles", ["title"])
    for table in ("practice_exams", "mock_exams"):
        op.create_table(table, primary_key(), sa.Column("title", sa.String(), nullable=False),
                        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), timestamp())
        op.create_index(f"ix_{table}_id", table, ["id"])
        op.create_index(f"ix_{table}_title", table, ["title"])
    for table, parent in (("practice_questions", "practice_exams"), ("mock_questions", "mock_exams")):
        columns = [primary_key(), sa.Column("exam_id", sa.Integer(), sa.ForeignKey(f"{parent}.id"), nullable=False),
                   sa.Column("content", sa.Text(), nullable=False), sa.Column("max_score", sa.Float(), nullable=False)]
        if table == "mock_questions":
            columns.append(sa.Column("section", sa.Integer(), nullable=False))
        op.create_table(table, *columns)
        op.create_index(f"ix_{table}_id", table, ["id"])
    op.create_table("submissions", primary_key(),
                    sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
                    sa.Column("exam_type", sa.String(), nullable=False),
                    sa.Column("practice_exam_id", sa.Integer(), sa.ForeignKey("practice_exams.id")),
                    sa.Column("mock_exam_id", sa.Integer(), sa.ForeignKey("mock_exams.id")),
                    sa.Column("leave_tab_count", sa.Integer(), nullable=False),
                    sa.Column("status", sa.String(), nullable=False), timestamp())
    op.create_index("ix_submissions_id", "submissions", ["id"])
    op.create_table("submission_answers", primary_key(),
                    sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
                    sa.Column("practice_question_id", sa.Integer(), sa.ForeignKey("practice_questions.id")),
                    sa.Column("mock_question_id", sa.Integer(), sa.ForeignKey("mock_questions.id")),
                    sa.Column("student_answer", sa.Text(), nullable=False))
    op.create_index("ix_submission_answers_id", "submission_answers", ["id"])
    op.create_table("submission_scores", primary_key(),
                    sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
                    sa.Column("answer_id", sa.Integer(), sa.ForeignKey("submission_answers.id"), nullable=False),
                    sa.Column("score", sa.Float(), nullable=False), sa.Column("teacher_comment", sa.Text()),
                    sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), timestamp())
    op.create_index("ix_submission_scores_id", "submission_scores", ["id"])


def downgrade():
    for table in ("submission_scores", "submission_answers", "submissions", "mock_questions", "practice_questions",
                  "mock_exams", "practice_exams", "theory_articles"):
        op.drop_table(table)
    op.drop_constraint("users_class_id_fkey", "users", type_="foreignkey")
    op.drop_table("classes")
    op.drop_table("users")
