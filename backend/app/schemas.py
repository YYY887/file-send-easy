from datetime import datetime

from pydantic import BaseModel


class ParcelFileOut(BaseModel):
    id: int
    original_name: str
    size: int
    download_url: str


class ParcelCreateOut(BaseModel):
    code: str
    pickup_url: str
    expires_at: datetime


class ParcelMetaOut(BaseModel):
    code: str
    has_text: bool
    file_count: int
    expires_at: datetime
    is_expired: bool


class ParcelPickupIn(BaseModel):
    code: str


class ParcelPickupOut(BaseModel):
    code: str
    text_content: str | None
    files: list[ParcelFileOut]
    expires_at: datetime
