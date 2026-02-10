"""Add conferences table

Revision ID: 0005_conferences
Revises: 0004_user_profile
Create Date: 2026-02-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_conferences"
down_revision = "0004_user_profile"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("submission_deadline", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("conferences")
