from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(64))
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    files: Mapped[list["ParcelFile"]] = relationship(
        back_populates="parcel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ParcelFile(Base):
    __tablename__ = "parcel_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int] = mapped_column(Integer)

    parcel: Mapped[Parcel] = relationship(back_populates="files")
