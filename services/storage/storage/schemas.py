from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True
