from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class TheoryArticle(Base):
    __tablename__ = "theory_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content_type = Column(String, nullable=False) # 'Text', 'Image', 'PDF', 'Link'
    content = Column(Text, nullable=False) # Can be text content or file URL
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="theory_articles")
