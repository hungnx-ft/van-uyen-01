from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'Teacher' or 'Student'
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student_class = relationship("Class", back_populates="students", foreign_keys=[class_id])
    managed_classes = relationship("Class", back_populates="teacher", foreign_keys="[Class.teacher_id]")
    theory_articles = relationship("TheoryArticle", back_populates="teacher")
    practice_exams = relationship("PracticeExam", back_populates="teacher")
    mock_exams = relationship("MockExam", back_populates="teacher")
    submissions = relationship("Submission", back_populates="student")
