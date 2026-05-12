from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.project_membership import ProjectMembership


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_users_org_email"),
    )

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Relationships
    organization: Mapped[Organization] = relationship(back_populates="users")
    project_memberships: Mapped[list[ProjectMembership]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    # NOTE: ondelete="CASCADE" on org_id means hard-deleting an organization
    # will hard-delete its users at the database level. Soft-delete (setting
    # deleted_at) on the organization does NOT cascade — it's just a column
    # update. Cascade cleanup of soft-deleted orgs must be handled in
    # application code if needed.
