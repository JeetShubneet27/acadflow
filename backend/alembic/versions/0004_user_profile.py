"""Add user profile fields

Revision ID: 0004_user_profile
Revises: 0003_workspace_documents
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_user_profile"
down_revision = "0003_workspace_documents"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "bio" not in columns:
        op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    if "institution" not in columns:
        op.add_column("users", sa.Column("institution", sa.String(), nullable=True))
    if "department" not in columns:
        op.add_column("users", sa.Column("department", sa.String(), nullable=True))
    if "research_interests" not in columns:
        op.add_column("users", sa.Column("research_interests", sa.Text(), nullable=True))
    if "website" not in columns:
        op.add_column("users", sa.Column("website", sa.String(), nullable=True))
    if "orcid" not in columns:
        op.add_column("users", sa.Column("orcid", sa.String(), nullable=True))
    if "linkedin" not in columns:
        op.add_column("users", sa.Column("linkedin", sa.String(), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "linkedin" in columns:
        op.drop_column("users", "linkedin")
    if "orcid" in columns:
        op.drop_column("users", "orcid")
    if "website" in columns:
        op.drop_column("users", "website")
    if "research_interests" in columns:
        op.drop_column("users", "research_interests")
    if "department" in columns:
        op.drop_column("users", "department")
    if "institution" in columns:
        op.drop_column("users", "institution")
    if "bio" in columns:
        op.drop_column("users", "bio")
