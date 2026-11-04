from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class TheoryArticle(Base):
    __tablename__ = "theory_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    # 'mixed' for posts that combine text and attachments; legacy rows keep
    # 'text', 'image', 'pdf' or 'link' with the file URL or data URI in content.
    content_type = Column(String, nullable=False)
    content = Column(Text, nullable=False, default="", server_default="")
    main_category = Column(String(50), nullable=True, index=True)
    sub_category = Column(String(80), nullable=True, index=True)
    description = Column(Text, nullable=False, default="", server_default="")
    icon = Column(String(20), nullable=False, default="📚", server_default="📚")
    is_published = Column(Boolean, nullable=False, default=True, server_default="true")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="theory_articles")
    attachments = relationship("TheoryAttachment", back_populates="article", cascade="all, delete-orphan",
                               order_by="(TheoryAttachment.position, TheoryAttachment.id)")


class TheoryAttachment(Base):
    __tablename__ = "theory_attachments"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("theory_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(10), nullable=False)  # 'image', 'file' or 'link'
    url = Column(String(2048), nullable=True)  # links only
    stored_name = Column(String(64), nullable=True, unique=True)  # uploads only, a UUID in UPLOAD_DIR
    original_name = Column(String(255), nullable=False, default="", server_default="")
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    position = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("kind IN ('image', 'file', 'link')", name="ck_theory_attachments_kind"),
        CheckConstraint("(kind = 'link') = (url IS NOT NULL)", name="ck_theory_attachments_link_url"),
        CheckConstraint("(kind = 'link') = (stored_name IS NULL)", name="ck_theory_attachments_stored_file"),
    )

    article = relationship("TheoryArticle", back_populates="attachments")
