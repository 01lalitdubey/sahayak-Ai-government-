import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from app.database.database import AsyncSessionLocal
from app.models.translation import SchemeTranslation

async def main():
    async with AsyncSessionLocal() as db:
        # Count translations
        count_res = await db.execute(select(func.count(SchemeTranslation.id)))
        count = count_res.scalar()
        print(f"Total translations: {count}")
        
        # Count published
        pub_res = await db.execute(select(func.count(SchemeTranslation.id)).where(SchemeTranslation.is_published == True))
        pub_count = pub_res.scalar()
        print(f"Published translations: {pub_count}")
        
        # Print a few samples
        samples = await db.execute(select(SchemeTranslation).limit(3))
        for r in samples.scalars().all():
            print(f"ID: {r.id} | Lang: {r.language_code} | Status: {r.status} | Published: {r.is_published}")
            print(f"Name: {r.translated_content.get('name') if r.translated_content else None}")

if __name__ == "__main__":
    asyncio.run(main())
