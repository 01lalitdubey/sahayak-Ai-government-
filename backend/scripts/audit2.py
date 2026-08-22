import asyncio
import sys
sys.path.insert(0, '.')

async def audit():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as db:
        # 1. Check translated_content structure
        r = await db.execute(text("""
            SELECT scheme_id, language_code, translated_content 
            FROM scheme_translations 
            WHERE language_code = 'hi' 
            LIMIT 5
        """))
        print('=== TRANSLATED CONTENT STRUCTURE ===')
        for row in r:
            print(f'\nScheme {str(row[0])[:8]}, lang={row[1]}:')
            content = row[2]
            if content:
                print(f'  Keys in JSON: {list(content.keys())}')
                for k, v in content.items():
                    print(f'  {k}: {str(v)[:100]}')
        
        # 2. Check if translations have empty short_description
        r = await db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN translated_content->>'name' IS NOT NULL AND translated_content->>'name' != '' THEN 1 END) as has_name,
                COUNT(CASE WHEN translated_content->>'short_description' IS NOT NULL AND translated_content->>'short_description' != '' THEN 1 END) as has_short_desc,
                COUNT(CASE WHEN translated_content->>'full_description' IS NOT NULL AND translated_content->>'full_description' != '' THEN 1 END) as has_full_desc
            FROM scheme_translations
            WHERE language_code = 'hi'
        """))
        print('\n=== CONTENT COMPLETENESS (hi) ===')
        for row in r:
            print(f'  Total: {row[0]}')
            print(f'  Has name: {row[1]}')
            print(f'  Has short_description: {row[2]}')
            print(f'  Has full_description: {row[3]}')
        
        # 3. Check pilot 100 schemes - are they in the active scheme list?
        r = await db.execute(text("""
            SELECT st.scheme_id, s.is_active, s.name
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            WHERE st.language_code = 'hi'
            LIMIT 5
        """))
        print('\n=== TRANSLATED SCHEMES - ARE THEY ACTIVE? ===')
        for row in r:
            print(f'  scheme_id={str(row[0])[:8]}, is_active={row[1]}, name={str(row[2])[:60]}')
        
        # 4. Check that translated name starts with [NLLB-200 prefix - this is the bug indicator
        r = await db.execute(text("""
            SELECT language_code, 
                   COUNT(*) as total,
                   COUNT(CASE WHEN translated_content->>'name' LIKE '[NLLB-200%]:%' THEN 1 END) as has_prefix
            FROM scheme_translations
            GROUP BY language_code
        """))
        print('\n=== NLLB PREFIX IN NAMES ===')
        for row in r:
            print(f'  lang={row[0]}: total={row[1]}, names_with_prefix={row[2]}')

asyncio.run(audit())
