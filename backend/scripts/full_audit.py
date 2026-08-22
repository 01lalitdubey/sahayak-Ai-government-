"""
Full Translation System Audit — Sahayak AI
Step 1: Database Verification
"""
import asyncio, sys
sys.path.insert(0, '.')

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("STEP 1: DATABASE VERIFICATION")
        print("=" * 60)

        r = await db.execute(text("SELECT COUNT(*) FROM schemes"))
        print(f"\n1. Total schemes: {r.scalar()}")

        r = await db.execute(text("SELECT COUNT(*) FROM scheme_translations"))
        print(f"2. Total translations: {r.scalar()}")

        r = await db.execute(text("""
            SELECT language_code, COUNT(*) as cnt
            FROM scheme_translations
            GROUP BY language_code ORDER BY language_code
        """))
        print("\n3. Translations per language:")
        for row in r: print(f"   {row[0]}: {row[1]}")

        r = await db.execute(text("""
            SELECT language_code, COUNT(*) as cnt
            FROM scheme_translations
            WHERE is_published = TRUE
            GROUP BY language_code ORDER BY language_code
        """))
        print("\n4. Published translations per language:")
        rows = r.fetchall()
        if rows:
            for row in rows: print(f"   {row[0]}: {row[1]}")
        else:
            print("   *** ZERO published translations! ***")

        r = await db.execute(text("""
            SELECT status, is_published, COUNT(*) as cnt
            FROM scheme_translations
            GROUP BY status, is_published ORDER BY status
        """))
        print("\n5. Status breakdown (status, is_published, count):")
        for row in r: print(f"   status={row[0]}, is_published={row[1]}: {row[2]}")

        r = await db.execute(text("""
            SELECT COUNT(*) FROM schemes s
            WHERE NOT EXISTS (
                SELECT 1 FROM scheme_translations st
                WHERE st.scheme_id = s.id AND st.language_code = 'hi'
            )
        """))
        print(f"\n6. Schemes with NO Hindi translation: {r.scalar()}")

        print("\n" + "=" * 60)
        print("STEP 2: CONTENT VERIFICATION (20 random hi translations)")
        print("=" * 60)
        r = await db.execute(text("""
            SELECT st.scheme_id,
                   s.name AS english_name,
                   st.translated_content->>'name' AS trans_name,
                   st.translated_content->>'short_description' AS trans_short,
                   st.translated_content->>'full_description' AS trans_full,
                   st.is_published,
                   st.status
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            WHERE st.language_code = 'hi'
            ORDER BY RANDOM() LIMIT 5
        """))
        for i, row in enumerate(r, 1):
            print(f"\n  Record {i}:")
            print(f"    scheme_id : {str(row[0])[:8]}")
            print(f"    english   : {(row[1] or '')[:70]}")
            print(f"    trans_name: {(row[2] or 'NULL')[:70]}")
            print(f"    trans_short (len={len(row[3] or '')}): {(row[3] or 'NULL')[:70]}")
            print(f"    trans_full  (len={len(row[4] or '')}): {(row[4] or 'NULL')[:60]}")
            print(f"    published={row[5]}, status={row[6]}")

asyncio.run(main())
