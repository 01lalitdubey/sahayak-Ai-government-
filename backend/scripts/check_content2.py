"""Check content quality"""
import asyncio, sys
sys.path.insert(0, '.')

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # Check if names are truly identical to English
        r = await db.execute(text("""
            SELECT 
                st.language_code,
                s.name as english_name,
                st.translated_content->>'name' as translated_name,
                length(st.translated_content->>'full_description') as full_len,
                length(st.translated_content->>'short_description') as short_len
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            WHERE st.language_code = 'hi'
            LIMIT 5
        """))
        print("=== HI translations vs English names ===")
        for row in r:
            eng = row[1] or ''
            trans = row[2] or ''
            identical = (eng.strip() == trans.strip())
            print(f"  identical={identical}, full_desc_len={row[3]}, short_len={row[4]}")
            print(f"    EN:    {eng[:60]}")
            print(f"    HI:    {trans[:60]}")

        # Summary: are ALL names identical to English?
        r2 = await db.execute(text("""
            SELECT 
                st.language_code,
                COUNT(*) as total,
                COUNT(CASE WHEN s.name = st.translated_content->>'name' THEN 1 END) as identical_to_en
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            GROUP BY st.language_code
            ORDER BY st.language_code
        """))
        print("\n=== Are translated names identical to English names? ===")
        print(f"{'lang':5} {'total':6} {'identical_to_en':15} {'% same':8}")
        for row in r2:
            pct = (row[2] / row[1] * 100) if row[1] else 0
            print(f"  {row[0]:5} {row[1]:6} {row[2]:15} {pct:.0f}%")

asyncio.run(main())
