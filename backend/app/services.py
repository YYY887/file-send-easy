import asyncio
import contextlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models import Parcel, ParcelFile


def ensure_storage() -> None:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)


def build_pickup_url(code: str) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/pickup/{code}"


def generate_code(length: int = 6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def unique_code(db: Session) -> str:
    while True:
        code = generate_code()
        exists = db.scalar(select(Parcel.id).where(Parcel.code == code))
        if not exists:
            return code


async def save_upload(upload: UploadFile) -> tuple[str, int]:
    ensure_storage()
    suffix = Path(upload.filename or "").suffix
    stored_name = f"{secrets.token_urlsafe(12)}{suffix}"
    file_path = settings.storage_dir / stored_name
    size = 0
    max_size = settings.max_upload_mb * 1024 * 1024

    try:
        with file_path.open("wb") as buffer:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File is too large. Max size is {settings.max_upload_mb}MB.",
                    )
                buffer.write(chunk)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            file_path.unlink()
        raise

    await upload.close()
    return stored_name, size


async def create_parcel(
    db: Session,
    text_content: str | None,
    uploads: list[UploadFile],
) -> Parcel:
    text_content = (text_content or "").strip() or None

    if not text_content and not uploads:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send text or files at least once.")

    code = unique_code(db)
    parcel = Parcel(
        code=code,
        password="",
        text_content=text_content,
        expires_at=datetime.utcnow() + timedelta(hours=settings.keep_hours),
    )
    db.add(parcel)
    db.flush()

    for upload in uploads:
        stored_name, size = await save_upload(upload)
        parcel.files.append(
            ParcelFile(
                original_name=upload.filename or "file",
                stored_name=stored_name,
                content_type=upload.content_type,
                size=size,
            )
        )

    db.commit()
    db.refresh(parcel)
    return parcel


def query_parcel(db: Session, code: str) -> Parcel | None:
    stmt = (
        select(Parcel)
        .options(selectinload(Parcel.files))
        .where(Parcel.code == code.strip().upper())
    )
    return db.scalar(stmt)


def assert_active(parcel: Parcel | None) -> Parcel:
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found.")
    if parcel.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Parcel expired.")
    return parcel


def pickup_parcel(db: Session, code: str) -> Parcel:
    parcel = assert_active(query_parcel(db, code))
    if parcel.picked_up_at is None:
        parcel.picked_up_at = datetime.utcnow()
        db.commit()
        db.refresh(parcel)
    return parcel


def delete_parcel_files(parcel: Parcel) -> None:
    for item in parcel.files:
        path = settings.storage_dir / item.stored_name
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def cleanup_expired(db: Session) -> int:
    expired = db.scalars(
        select(Parcel)
        .options(selectinload(Parcel.files))
        .where(Parcel.expires_at <= datetime.utcnow())
    ).all()

    if not expired:
        return 0

    for parcel in expired:
        delete_parcel_files(parcel)
        db.delete(parcel)

    db.commit()
    return len(expired)


async def cleanup_loop(session_factory) -> None:
    while True:
        await asyncio.sleep(settings.cleanup_interval_minutes * 60)
        with contextlib.suppress(Exception):
            db = session_factory()
            try:
                cleanup_expired(db)
            finally:
                db.close()
