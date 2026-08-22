"""Check PostgreSQL enum values in the database."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database.database import AsyncSessionLocal


async def check():
    async with AsyncSessionLocal() as session:
        # Check what values exist in each enum
        r1 = await session.execute(text(
            "SELECT enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid "
            "WHERE t.typname = 'scheme_type_enum' ORDER BY enumsortorder"
        ))
        print("scheme_type_enum values:", [row[0] for row in r1.fetchall()])

        r2 = await session.execute(text(
            "SELECT enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid "
            "WHERE t.typname = 'scheme_category_enum' ORDER BY enumsortorder"
        ))
        print("scheme_category_enum values:", [row[0] for row in r2.fetchall()])

        r3 = await session.execute(text(
            "SELECT enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid "
            "WHERE t.typname = 'application_mode_enum' ORDER BY enumsortorder"
        ))
        print("application_mode_enum values:", [row[0] for row in r3.fetchall()])

        # Also check table schema
        r4 = await session.execute(text(
            "SELECT column_name, data_type, udt_name FROM information_schema.columns "
            "WHERE table_name = 'schemes' ORDER BY ordinal_position"
        ))
        print("\nSchemes table columns:")
        for row in r4.fetchall():
            print(f"  {row[0]}: {row[1]} ({row[2]})")


if __name__ == "__main__":
    asyncio.run(check())
