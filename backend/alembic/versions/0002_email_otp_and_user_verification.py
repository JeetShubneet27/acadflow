"""Add email OTPs and user verification fields

Revision ID: 0002_email_otp
Revises: 0001_initial
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_email_otp"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "users" in tables:
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "is_email_verified" not in columns:
            op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT FALSE")
        if "email_verified_at" not in columns:
            op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP")

    if "email_otps" not in tables:
        op.create_table(
            "email_otps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("purpose", sa.String(), nullable=False),
            sa.Column("otp_hash", sa.String(), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("consumed_at", sa.DateTime(), nullable=True),
            sa.Column("last_sent_at", sa.DateTime(), nullable=False),
        )
    indexes = {index["name"] for index in inspector.get_indexes("email_otps")} if "email_otps" in tables else set()
    if "ix_email_otps_email" not in indexes:
        op.create_index("ix_email_otps_email", "email_otps", ["email"])


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())
    if "email_otps" in tables:
        op.drop_index("ix_email_otps_email", table_name="email_otps")
        op.drop_table("email_otps")
    if "users" in tables:
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "email_verified_at" in columns:
            op.drop_column("users", "email_verified_at")
        if "is_email_verified" in columns:
            op.drop_column("users", "is_email_verified")
