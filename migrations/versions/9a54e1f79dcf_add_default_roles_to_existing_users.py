"""Add default roles to existing users

Revision ID: 9a54e1f79dcf
Revises: 2451be1e11e3
Create Date: 2025-09-08 02:48:54.005769

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a54e1f79dcf'
down_revision = '2451be1e11e3'
branch_labels = None
depends_on = None


def upgrade():
    # Set a default role for any existing users that might not have one
    op.execute("UPDATE \"user\" SET role='lawyer' WHERE role IS NULL OR role NOT IN ('admin', 'lawyer', 'staff')")

    # Optionally, explicitly update roles for known users from populate_db.py
    # This assumes 'username' is unique and these users exist
    op.execute("UPDATE \"user\" SET role='admin' WHERE username='admin'")
    op.execute("UPDATE \"user\" SET role='lawyer' WHERE username='lawyer1'")
    op.execute("UPDATE \"user\" SET role='staff' WHERE username='staff1'")


def downgrade():
    # If downgrading, you might revert roles or set them back to NULL if that was the previous state
    # This example sets all non-admin roles back to NULL for simplicity,
    # but in a real app, you might need a more complex rollback strategy.
    op.execute("UPDATE \"user\" SET role=NULL WHERE role IN ('lawyer', 'staff', 'admin')")
