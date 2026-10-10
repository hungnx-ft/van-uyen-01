from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class Assignment(Base):
    """A teacher assigns one exam to one class."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    exam_type = Column(String(20), nullable=False)
    practice_exam_id = Column(Integer, ForeignKey("practice_exams.id"), nullable=True)
    mock_exam_id = Column(Integer, ForeignKey("mock_exams.id"), nullable=True)
    exam_title = Column(String(300), nullable=False)
    instructions = Column(Text, nullable=False, default="", server_default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    teacher = relationship("User")
    classroom = relationship("Class")
    practice_exam = relationship("PracticeExam")
    mock_exam = relationship("MockExam")

    __table_args__ = (
        UniqueConstraint("class_id", "exam_type", "practice_exam_id", "mock_exam_id", name="uq_assignments_class_exam"),
    )
