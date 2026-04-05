import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.schemas import ParcelCreateOut, ParcelFileOut, ParcelMetaOut, ParcelPickupIn, ParcelPickupOut
from app.services import build_pickup_url, cleanup_expired, cleanup_loop, create_parcel, pickup_parcel, query_parcel


cleanup_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global cleanup_task

    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        cleanup_expired(db)
    finally:
        db.close()

    cleanup_task = asyncio.create_task(cleanup_loop(SessionLocal))
    yield

    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def file_to_out(file_id: int, name: str, size: int) -> ParcelFileOut:
    return ParcelFileOut(
        id=file_id,
        original_name=name,
        size=size,
        download_url=f"{settings.api_prefix}/files/{file_id}",
    )


@app.get(f"{settings.api_prefix}/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(f"{settings.api_prefix}/parcels", response_model=ParcelCreateOut)
async def create_parcel_api(
    text_content: str | None = Form(None),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    parcel = await create_parcel(db, text_content=text_content, uploads=files)
    return ParcelCreateOut(
        code=parcel.code,
        pickup_url=build_pickup_url(parcel.code),
        expires_at=parcel.expires_at,
    )


@app.get(f"{settings.api_prefix}/parcels/{{code}}", response_model=ParcelMetaOut)
def parcel_meta(code: str, db: Session = Depends(get_db)):
    parcel = query_parcel(db, code)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found.")
    return ParcelMetaOut(
        code=parcel.code,
        has_text=bool(parcel.text_content),
        file_count=len(parcel.files),
        expires_at=parcel.expires_at,
        is_expired=parcel.expires_at <= datetime.utcnow(),
    )


@app.post(f"{settings.api_prefix}/pickup", response_model=ParcelPickupOut)
def pickup_api(payload: ParcelPickupIn, db: Session = Depends(get_db)):
    parcel = pickup_parcel(db, code=payload.code)
    return ParcelPickupOut(
        code=parcel.code,
        text_content=parcel.text_content,
        files=[file_to_out(item.id, item.original_name, item.size) for item in parcel.files],
        expires_at=parcel.expires_at,
    )


@app.get(f"{settings.api_prefix}/files/{{file_id}}")
def download_file(file_id: int, db: Session = Depends(get_db)):
    from app.models import ParcelFile

    item = db.get(ParcelFile, file_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    path = settings.storage_dir / item.stored_name
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return FileResponse(path=path, filename=item.original_name, media_type=item.content_type)


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa(_: str = ""):
        return FileResponse(frontend_dist / "index.html")
