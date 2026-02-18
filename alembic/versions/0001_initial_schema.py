"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-02-18 20:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "colleges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("join_code", sa.String(length=64), nullable=False),
        sa.Column("total_tiles", sa.Integer(), nullable=False),
        sa.CheckConstraint("total_tiles >= 0", name="ck_colleges_total_tiles_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("join_code"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_colleges_id"), "colleges", ["id"], unique=False)
    op.create_index(op.f("ix_colleges_join_code"), "colleges", ["join_code"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("mana", sa.Integer(), nullable=False),
        sa.Column("last_regen_time", sa.DateTime(), nullable=False),
        sa.Column("daily_mana_earned", sa.Integer(), nullable=False),
        sa.Column("college_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("daily_mana_earned <= 200", name="ck_users_daily_mana_max_cap"),
        sa.CheckConstraint("daily_mana_earned >= 0", name="ck_users_daily_mana_non_negative"),
        sa.CheckConstraint("mana <= 200", name="ck_users_mana_max_cap"),
        sa.CheckConstraint("mana >= 0", name="ck_users_mana_non_negative"),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_college_id"), "users", ["college_id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "hex_tiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("q", sa.Integer(), nullable=False),
        sa.Column("r", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("defense_level", sa.Integer(), nullable=False),
        sa.CheckConstraint("defense_level >= 1", name="ck_hex_tiles_defense_level_min"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("q", "r", name="uq_hex_tiles_q_r"),
    )
    op.create_index("ix_hex_tiles_q_r", "hex_tiles", ["q", "r"], unique=False)
    op.create_index(op.f("ix_hex_tiles_id"), "hex_tiles", ["id"], unique=False)
    op.create_index(op.f("ix_hex_tiles_owner_id"), "hex_tiles", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hex_tiles_owner_id"), table_name="hex_tiles")
    op.drop_index(op.f("ix_hex_tiles_id"), table_name="hex_tiles")
    op.drop_index("ix_hex_tiles_q_r", table_name="hex_tiles")
    op.drop_table("hex_tiles")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_college_id"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_colleges_join_code"), table_name="colleges")
    op.drop_index(op.f("ix_colleges_id"), table_name="colleges")
    op.drop_table("colleges")
