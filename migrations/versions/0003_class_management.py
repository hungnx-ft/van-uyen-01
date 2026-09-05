"""School year and reversible class archiving; preserve all memberships."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("classes", sa.Column("year", sa.String(9), nullable=True))
    op.add_column("classes", sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("classes", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_classes_teacher_id", "classes", ["teacher_id"])
    op.create_index("ix_users_class_id", "users", ["class_id"])
    # Legacy classes have year=NULL, so existing same-name classes are preserved.
    op.create_unique_constraint("uq_classes_teacher_name_year", "classes", ["teacher_id", "name", "year"])


def downgrade():
    op.drop_constraint("uq_classes_teacher_name_year", "classes", type_="unique")
    op.drop_index("ix_users_class_id", table_name="users")
    op.drop_index("ix_classes_teacher_id", table_name="classes")
    for column in ("archived_at", "is_archived", "year"):
        op.drop_column("classes", column)
