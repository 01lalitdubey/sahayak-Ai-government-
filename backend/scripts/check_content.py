"""
Check if full_description in translations contains any non-ASCII characters
(i.e. actual Hindi/Devanagari script)
"""
import asyncio, sys
sys.path.insert(0, '.')

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # Check for non-ASCII characters in translated content
        r = await db.execute(text("""
            SELECT 
                language_code,
                COUNT(*) as total,
                COUNT(CASE WHEN translated_content->>'name' ~ '[^\x00-\x7F]' THEN 1 END) as has_non_ascii_name,
                COUNT(CASE WHEN translated_content->>'full_description' ~ '[^\x00-\x7F]' THEN 1 END) as has_non_ascii_full,
                COUNT(CASE WHEN translated_content->>'short_description' != '' THEN 1 END) as has_short_desc
            FROM scheme_translations
            GROUP BY language_code
            ORDER BY language_code
        """))
        print("=== Non-ASCII content in translations ===")
        print(f"{'lang':5} {'total':6} {'non_ascii_name':15} {'non_ascii_full':15} {'has_short':10}")
        for row in r:
            print(f"{row[0]:5} {row[1]:6} {row[2]:15} {row[3]:15} {row[4]:10}")

        # Check one hi record with full_description that has non-ASCII chars
        r2 = await db.execute(text("""
            SELECT st.translated_content->>'full_description' as full_desc
            FROM scheme_translations st
            WHERE st.language_code = 'hi'
              AND translated_content->>'full_description' ~ '[^\x00-\x7F]'
            LIMIT 1
        """))
        row = r2.fetchone()
        if row:
            print("\n=== Sample non-ASCII full_description (hi) ===")
            print(f"  First 200 chars: {row[0][:200] if row[0] else 'NONE'}")
        else:
            print("\nNo non-ASCII content found in hi full_description")

        # Deeper: check if any language has actual script characters
        print("\n=== Languages with actual script (non-ASCII) ===")
        r3 = await db.execute(text("""
            SELECT language_code, 
                   translated_content->>'name' as name,
                   translated_content->>'full_description' as full
            FROM scheme_translations
            WHERE translated_content->>'name' ~ '[^\x00-\x7F]'
            LIMIT 5
        """))
        rows = r3.fetchall()
        if rows:
            for row in rows:
                print(f"  lang={row[0]}, name={row[1][:60]}")
        else:
            print("  NONE — all translations contain only ASCII (English text)")

asyncio.run(main())
