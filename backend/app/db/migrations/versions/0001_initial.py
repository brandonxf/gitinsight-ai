"""initial schema: repository, analysis_job, analysis_result, finding

Revision ID: 0001
Revises:
Create Date: 2026-06-25
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repository",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_branch", sa.String(length=255), nullable=True),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repository_url", "repository", ["url"], unique=True)

    op.create_table(
        "analysis_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("phase", sa.String(length=64), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("options", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repository.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_analysis_job_repository_created", "analysis_job", ["repository_id", "created_at"]
    )
    op.create_index("ix_analysis_job_status", "analysis_job", ["status"])

    op.create_table(
        "analysis_result",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_language", sa.String(length=64), nullable=True),
        sa.Column("languages", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("frameworks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("structure", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("modules", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("flow_description", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("diagrams", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("generated_docs", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_job.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("job_id", name="uq_analysis_result_job_id"),
    )

    op.create_table(
        "finding",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_job.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_finding_job_category_severity", "finding", ["job_id", "category", "severity"]
    )


def downgrade() -> None:
    op.drop_table("finding")
    op.drop_table("analysis_result")
    op.drop_index("ix_analysis_job_status", table_name="analysis_job")
    op.drop_index("ix_analysis_job_repository_created", table_name="analysis_job")
    op.drop_table("analysis_job")
    op.drop_index("ix_repository_url", table_name="repository")
    op.drop_table("repository")
