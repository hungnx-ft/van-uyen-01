from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String, DateTime, ForeignKey, true
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'Teacher' or 'Student'
    class_id = Column(Integer, ForeignKey("classes.id", name="users_class_id_fkey", use_alter=True), nullable=True, index=True)
    full_name = Column(String(200), nullable=False)
    school_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    __table_args__ = (CheckConstraint("role IN ('Teacher', 'Student')", name="ck_users_role"),)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student_class = relationship("Class", back_populates="students", foreign_keys=[class_id])
    managed_classes = relationship("Class", back_populates="teacher", foreign_keys="[Class.teacher_id]")
    theory_articles = relationship("TheoryArticle", back_populates="teacher")
    practice_exams = relationship("PracticeExam", back_populates="teacher")
    mock_exams = relationship("MockExam", back_populates="teacher")
    submissions = relationship("Submission", back_populates="student")

    @property
    def class_name(self):
        return self.student_class.name if self.student_class else None

    @property
    def class_year(self):
        return self.student_class.year if self.student_class else None
