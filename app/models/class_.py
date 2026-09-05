from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, false
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(String(9), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False, server_default=false())
    archived_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("teacher_id", "name", "year", name="uq_classes_teacher_name_year"),)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="managed_classes", foreign_keys=[teacher_id])
    students = relationship("User", back_populates="student_class", foreign_keys="[User.class_id]")
