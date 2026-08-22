"""Check what translated_content actually has after fix"""
import asyncio
import sys
sys.path.insert(0, '.')

async def debug():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT st.scheme_id, s.name as english_name, 
                   st.translated_content->>'name' as trans_name,
                   st.translated_content->>'short_description' as trans_short,
                   st.translated_content->>'full_description' as trans_full
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            WHERE st.language_code = 'hi'
            LIMIT 10
        """))
        
        print('=== CONTENT AFTER FIX ===')
        for row in r:
            eng = row[1]
            trans_name = row[2] or ''
            trans_short = row[3] or ''
            trans_full = (row[4] or '')[:80]
            print(f'English: {eng[:60]}')
            print(f'Trans name: [{len(trans_name)}chars]: {trans_name[:60]}')
            print(f'Trans short: [{len(trans_short)}chars]: {trans_short[:60]}')
            print(f'Trans full: [{len(trans_full)}chars]: {trans_full[:60]}')
            print()

asyncio.run(debug())
