from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Image


class ImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, image: Image) -> Image:
        self.session.add(image)
        await self.session.commit()
        await self.session.refresh(image)
        return image

    async def get(self, image_id: UUID) -> Image | None:
        result = await self.session.execute(select(Image).where(Image.id == image_id))
        return result.scalar_one_or_none()

    async def list_expired(self, now: datetime) -> list[Image]:
        result = await self.session.execute(
            select(Image).where(Image.expires_at <= now)
        )
        return list(result.scalars().all())

    async def delete(self, image: Image) -> None:
        await self.session.delete(image)
        await self.session.commit()
