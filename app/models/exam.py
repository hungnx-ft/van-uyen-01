from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class PracticeExam(Base):
    __tablename__ = "practice_exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    target_group = Column(String(50), nullable=True, index=True)
    passage = Column(Text, nullable=False, default="", server_default="")
    genre = Column(String(50), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=45, server_default="45")
    is_published = Column(Boolean, nullable=False, default=True, server_default="true")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="practice_exams")
    questions = relationship("PracticeQuestion", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="practice_exam")

class PracticeQuestion(Base):
    __tablename__ = "practice_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("practice_exams.id"), nullable=False)
    content = Column(Text, nullable=False)
    max_score = Column(Float, nullable=False, default=0.8)
    answer_key = Column(Text, nullable=False, default="", server_default="")

    __table_args__ = (CheckConstraint("max_score >= 0", name="ck_practice_questions_max_score_nonnegative"),)

    exam = relationship("PracticeExam", back_populates="questions")

class MockExam(Base):
    __tablename__ = "mock_exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    target_group = Column(String(50), nullable=True, index=True)
    passage = Column(Text, nullable=False, default="", server_default="")
    genre = Column(String(50), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=120, server_default="120")
    is_published = Column(Boolean, nullable=False, default=True, server_default="true")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="mock_exams")
    questions = relationship("MockQuestion", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="mock_exam")

class MockQuestion(Base):
    __tablename__ = "mock_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("mock_exams.id"), nullable=False)
    section = Column(Integer, nullable=False) # 1 for Reading, 2 for Writing
    content = Column(Text, nullable=False)
    max_score = Column(Float, nullable=False)
    answer_key = Column(Text, nullable=False, default="", server_default="")

    __table_args__ = (
        CheckConstraint("section IN (1, 2)", name="ck_mock_questions_section"),
        CheckConstraint("max_score >= 0", name="ck_mock_questions_max_score_nonnegative"),
    )

    exam = relationship("MockExam", back_populates="questions")
