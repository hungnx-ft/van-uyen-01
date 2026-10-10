from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class TheoryArticle(Base):
    __tablename__ = "theory_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content_type = Column(String, nullable=False) # 'Text', 'Image', 'PDF', 'Link'
    content = Column(Text, nullable=False) # Can be text content or file URL
    main_category = Column(String(50), nullable=True, index=True)
    sub_category = Column(String(80), nullable=True, index=True)
    description = Column(Text, nullable=False, default="", server_default="")
    icon = Column(String(20), nullable=False, default="📚", server_default="📚")
    is_published = Column(Boolean, nullable=False, default=True, server_default="true")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="theory_articles")
