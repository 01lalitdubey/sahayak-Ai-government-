import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import update
from app.database.database import AsyncSessionLocal
from app.models.translation import SchemeTranslation
from app.models.enums import TranslationStatusEnum

async def main():
    async with AsyncSessionLocal() as db:
        stmt = (
            update(SchemeTranslation)
            .values(is_published=True, status=TranslationStatusEnum.PUBLISHED)
        )
        result = await db.execute(stmt)
        await db.commit()
        print(f"Successfully published translations")

if __name__ == "__main__":
    asyncio.run(main())
