"""Add workspace documents and revisions

Revision ID: 0003_workspace_documents
Revises: 0002_email_otp
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_workspace_documents"
down_revision = "0002_email_otp"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "format",
            sa.Enum("word", "latex", name="workspaceformat"),
            nullable=False,
        ),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "workspace_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("workspace_documents.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("original_filename", sa.String(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "workspace_locks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("workspace_documents.id"), nullable=False),
        sa.Column("locked_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "released", "expired", name="draftlockstatus", create_type=False),
            nullable=False,
        ),
        sa.Column("locked_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("workspace_locks")
    op.drop_table("workspace_revisions")
    op.drop_table("workspace_documents")
