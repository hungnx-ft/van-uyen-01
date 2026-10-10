from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, false

from app.database.session import Base


class AISetting(Base):
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(150), nullable=False)
    base_url = Column(String(500), nullable=True)
    api_key_encrypted = Column(String(1024), nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=False, server_default=false())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    teacher = relationship("User")


class ExamRubric(Base):
    __tablename__ = "exam_rubrics"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_type = Column(String(20), nullable=False)
    practice_exam_id = Column(Integer, ForeignKey("practice_exams.id", ondelete="CASCADE"), nullable=True, index=True)
    mock_exam_id = Column(Integer, ForeignKey("mock_exams.id", ondelete="CASCADE"), nullable=True, index=True)
    content_text = Column(Text, nullable=False)
    original_filename = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    storage_path = Column(String(1000), nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    teacher = relationship("User")
    __table_args__ = (
        CheckConstraint("((practice_exam_id IS NOT NULL AND mock_exam_id IS NULL) OR (practice_exam_id IS NULL AND mock_exam_id IS NOT NULL))", name="ck_exam_rubrics_one_exam"),
        CheckConstraint("exam_type IN ('Practice', 'Mock')", name="ck_exam_rubrics_exam_type"),
        CheckConstraint("version >= 1", name="ck_exam_rubrics_version_positive"),
    )


class AIGradingJob(Base):
    __tablename__ = "ai_grading_jobs"

    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    rubric_id = Column(Integer, ForeignKey("exam_rubrics.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(150), nullable=False)
    rubric_version = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost_usd = Column(Float, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")

    submission = relationship("Submission")
    rubric = relationship("ExamRubric")
    result = relationship("AIGradingResult", back_populates="job", uselist=False, cascade="all, delete-orphan")
    __table_args__ = (CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="ck_ai_grading_jobs_status"),)


class AIGradingResult(Base):
    __tablename__ = "ai_grading_results"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("ai_grading_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    total_score = Column(Float, nullable=True)
    overall_comment = Column(Text, nullable=True)
    improvement_suggestion = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    job = relationship("AIGradingJob", back_populates="result")
    submission = relationship("Submission")
    answers = relationship("AIGradingAnswer", back_populates="result", cascade="all, delete-orphan")


class AIGradingAnswer(Base):
    __tablename__ = "ai_grading_answers"

    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey("ai_grading_results.id", ondelete="CASCADE"), nullable=False, index=True)
    practice_question_id = Column(Integer, ForeignKey("practice_questions.id", ondelete="CASCADE"), nullable=True)
    mock_question_id = Column(Integer, ForeignKey("mock_questions.id", ondelete="CASCADE"), nullable=True)
    ai_score = Column(Float, nullable=False)
    ai_question_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    result = relationship("AIGradingResult", back_populates="answers")
    __table_args__ = (
        CheckConstraint("((practice_question_id IS NOT NULL AND mock_question_id IS NULL) OR (practice_question_id IS NULL AND mock_question_id IS NOT NULL))", name="ck_ai_grading_answers_one_question"),
        CheckConstraint("ai_score >= 0", name="ck_ai_grading_answers_score_nonnegative"),
    )
