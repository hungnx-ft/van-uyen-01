"""Account profile, status and revocable refresh sessions."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("full_name", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("school_name", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("UPDATE users SET full_name = left(username, 200)")
    op.alter_column("users", "full_name", nullable=False)
    op.create_check_constraint("ck_users_role", "users", "role IN ('Teacher', 'Student')")
    op.create_table("auth_sessions",
                    sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("refresh_token_hash", sa.String(64), nullable=False, unique=True),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])


def downgrade():
    op.drop_table("auth_sessions")
    op.drop_constraint("ck_users_role", "users", type_="check")
    for column in ("is_active", "school_name", "full_name"):
        op.drop_column("users", column)
