"""
Step 1: Complete Database Verification — Sahayak AI
"""
import asyncio, sys
sys.path.insert(0, '.')

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("DATABASE VERIFICATION")
        print("=" * 60)

        # 1. Total schemes
        r = await db.execute(text("SELECT COUNT(*) FROM schemes WHERE is_active = TRUE"))
        total_schemes = r.scalar()
        print(f"\n1. Total ACTIVE schemes: {total_schemes}")

        # 2. Total translations
        r = await db.execute(text("SELECT COUNT(*) FROM scheme_translations"))
        total_trans = r.scalar()
        print(f"2. Total translations:   {total_trans}")

        # 3. By language
        r = await db.execute(text("""
            SELECT language_code, COUNT(*) as cnt, 
                   SUM(CASE WHEN is_published THEN 1 ELSE 0 END) as published
            FROM scheme_translations
            GROUP BY language_code ORDER BY language_code
        """))
        rows = r.fetchall()
        print(f"\n3. Translations per language:")
        print(f"   {'lang':5} {'total':8} {'published':10}")
        for row in rows:
            print(f"   {row[0]:5} {row[1]:8} {row[2]:10}")

        # 4. Missing translations (no hi translation)
        r = await db.execute(text("""
            SELECT COUNT(*) FROM schemes s
            WHERE s.is_active = TRUE AND NOT EXISTS (
                SELECT 1 FROM scheme_translations st
                WHERE st.scheme_id = s.id AND st.language_code = 'hi'
            )
        """))
        print(f"\n4. Schemes missing Hindi translation: {r.scalar()} / {total_schemes}")

        # 5. English-only translations (name identical to English)
        r = await db.execute(text("""
            SELECT language_code, 
                COUNT(*) as total,
                COUNT(CASE WHEN s.name = st.translated_content->>'name' THEN 1 END) as same_as_english,
                COUNT(CASE WHEN (st.translated_content->>'name') = '' OR (st.translated_content->>'name') IS NULL THEN 1 END) as empty_name
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            GROUP BY language_code ORDER BY language_code
        """))
        rows = r.fetchall()
        print(f"\n5. Translation quality (identical to English = FAKE):")
        print(f"   {'lang':5} {'total':8} {'fake/same':10} {'empty':8}")
        for row in rows:
            print(f"   {row[0]:5} {row[1]:8} {row[2]:10} {row[3]:8}")

        # 6. Published stats
        r = await db.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_published THEN 1 ELSE 0 END) as published,
                SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as status_published
            FROM scheme_translations
        """))
        row = r.fetchone()
        print(f"\n6. Published: {row[1]}/{row[0]} (status=published: {row[2]})")

        expected = total_schemes * 11  # 11 languages
        print(f"\n   Expected total (all schemes × 11 langs): {expected}")
        print(f"   Missing records: {expected - total_trans}")

asyncio.run(main())
