import asyncio
from sqlalchemy import select
from app.database.database import AsyncSessionLocal
from app.models.translation_job import TranslationJob

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TranslationJob).order_by(TranslationJob.created_at.desc()).limit(1))
        job = res.scalar_one_or_none()
        if job:
            print(f"Job ID: {job.id}")
            print(f"Status: {job.status.value}")
            print(f"Processed: {job.processed_records} / {job.total_records}")
            print(f"Failed: {job.failed_records}")
            if job.logs:
                print(f"Last Log: {job.logs[-1]}")
        else:
            print("No jobs found.")

if __name__ == "__main__":
    asyncio.run(main())
