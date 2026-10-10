from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String, DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_type = Column(String, nullable=False) # 'Practice' or 'Mock'
    practice_exam_id = Column(Integer, ForeignKey("practice_exams.id"), nullable=True)
    mock_exam_id = Column(Integer, ForeignKey("mock_exams.id"), nullable=True)
    leave_tab_count = Column(Integer, default=0, nullable=False)
    status = Column(String, nullable=False, default="Submitted") # 'Submitted', 'Graded'
    attempt = Column(Integer, nullable=False, default=1, server_default="1")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    self_score = Column(Float, nullable=True)
    teacher_score = Column(Float, nullable=True)
    teacher_comment = Column(Text, nullable=True)
    teacher_improvement_note = Column(Text, nullable=True)
    feedback_published = Column(Boolean, nullable=False, default=False, server_default="false")
    feedback_published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("attempt >= 1", name="ck_submissions_attempt_positive"),
        CheckConstraint("leave_tab_count >= 0", name="ck_submissions_leave_tab_nonnegative"),
        CheckConstraint("self_score IS NULL OR self_score >= 0", name="ck_submissions_self_score_nonnegative"),
        CheckConstraint("teacher_score IS NULL OR teacher_score >= 0", name="ck_submissions_teacher_score_nonnegative"),
    )

    student = relationship("User", back_populates="submissions")
    practice_exam = relationship("PracticeExam", back_populates="submissions")
    mock_exam = relationship("MockExam", back_populates="submissions")
    answers = relationship("SubmissionAnswer", back_populates="submission", cascade="all, delete-orphan")
    scores = relationship("SubmissionScore", back_populates="submission", cascade="all, delete-orphan")

    @property
    def student_name(self):
        return self.student.full_name if self.student else ""

class SubmissionAnswer(Base):
    __tablename__ = "submission_answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    practice_question_id = Column(Integer, ForeignKey("practice_questions.id"), nullable=True)
    mock_question_id = Column(Integer, ForeignKey("mock_questions.id"), nullable=True)
    student_answer = Column(Text, nullable=False)

    submission = relationship("Submission", back_populates="answers")
    score = relationship("SubmissionScore", back_populates="answer", uselist=False, cascade="all, delete-orphan")

class SubmissionScore(Base):
    __tablename__ = "submission_scores"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    answer_id = Column(Integer, ForeignKey("submission_answers.id"), nullable=False)
    score = Column(Float, nullable=False)
    teacher_comment = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("answer_id", name="uq_submission_scores_answer_id"),
        CheckConstraint("score >= 0", name="ck_submission_scores_nonnegative"),
    )

    submission = relationship("Submission", back_populates="scores")
    answer = relationship("SubmissionAnswer", back_populates="score")
