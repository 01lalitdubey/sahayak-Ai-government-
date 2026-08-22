import asyncio
import sys
sys.path.insert(0, '.')

async def audit():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as db:
        # 1. Total schemes
        r = await db.execute(text('SELECT COUNT(*) FROM schemes WHERE is_active = true'))
        print('ACTIVE SCHEMES:', r.scalar())
        
        # 2. Total translations
        r = await db.execute(text('SELECT COUNT(*) FROM scheme_translations'))
        print('TOTAL TRANSLATIONS:', r.scalar())
        
        # 3. Translations per language
        r = await db.execute(text('SELECT language_code, COUNT(*) as cnt FROM scheme_translations GROUP BY language_code ORDER BY language_code'))
        print('TRANSLATIONS PER LANGUAGE:')
        for row in r:
            print(f'  {row[0]}: {row[1]}')
        
        # 4. Published status
        r = await db.execute(text('SELECT status, is_published, COUNT(*) as cnt FROM scheme_translations GROUP BY status, is_published ORDER BY status'))
        print('BY STATUS + PUBLISHED:')
        for row in r:
            print(f'  status={row[0]}, is_published={row[1]}: {row[2]}')
        
        # 5. Sample translated_content for hi
        r = await db.execute(text("SELECT scheme_id, language_code, is_published, status, translated_content FROM scheme_translations WHERE language_code = 'hi' LIMIT 3"))
        print('SAMPLE HI TRANSLATIONS:')
        for row in r:
            content = row[4]
            print(f'  scheme_id={str(row[0])[:8]}, lang={row[1]}, published={row[2]}, status={row[3]}')
            if content:
                for key in ['name', 'short_description']:
                    if key in content:
                        val = str(content[key])[:80]
                        print(f'    {key}: {val}')

asyncio.run(audit())
