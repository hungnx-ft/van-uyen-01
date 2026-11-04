"""Let one knowledge post combine text with images, links and files."""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "theory_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("theory_articles.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("stored_name", sa.String(64), nullable=True, unique=True),
        sa.Column("original_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('image', 'file', 'link')", name="ck_theory_attachments_kind"),
        sa.CheckConstraint("(kind = 'link') = (url IS NOT NULL)", name="ck_theory_attachments_link_url"),
        sa.CheckConstraint("(kind = 'link') = (stored_name IS NULL)", name="ck_theory_attachments_stored_file"),
    )
    op.alter_column("theory_articles", "content", server_default="")


def downgrade():
    op.alter_column("theory_articles", "content", server_default=None)
    op.drop_table("theory_attachments")
