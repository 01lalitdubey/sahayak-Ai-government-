"""Check scheme_translations table constraints"""
import asyncio, sys
sys.path.insert(0, '.')

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # Table columns
        r = await db.execute(text("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'scheme_translations'
            ORDER BY ordinal_position
        """))
        print("Columns:")
        for row in r:
            print(f"  {row[0]:30} {row[1]:20} default={row[2]} nullable={row[3]}")
        
        # Unique constraints
        r = await db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'scheme_translations'
        """))
        print("\nIndexes:")
        for row in r:
            print(f"  {row[0]}: {row[1]}")

asyncio.run(main())
