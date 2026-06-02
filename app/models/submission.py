from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="submissions")
    practice_exam = relationship("PracticeExam", back_populates="submissions")
    mock_exam = relationship("MockExam", back_populates="submissions")
    answers = relationship("SubmissionAnswer", back_populates="submission", cascade="all, delete-orphan")
    scores = relationship("SubmissionScore", back_populates="submission", cascade="all, delete-orphan")

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

    submission = relationship("Submission", back_populates="scores")
    answer = relationship("SubmissionAnswer", back_populates="score")
