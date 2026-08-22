import asyncio
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

async def audit():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as db:
        # 1. Check translated_content structure - just check keys and ASCII portions
        r = await db.execute(text("""
            SELECT scheme_id, language_code, translated_content 
            FROM scheme_translations 
            WHERE language_code = 'hi' 
            LIMIT 3
        """))
        print('=== TRANSLATED CONTENT STRUCTURE ===')
        for row in r:
            print(f'Scheme {str(row[0])[:8]}, lang={row[1]}:')
            content = row[2]
            if content:
                print(f'  Keys: {list(content.keys())}')
                name = content.get('name', '')
                short_desc = content.get('short_description', '')
                # Check if name starts with the invalid [NLLB-200 prefix
                has_prefix = name.startswith('[NLLB-200')
                print(f'  name has_nllb_prefix: {has_prefix}')
                print(f'  name length: {len(name)}')
                print(f'  short_description length: {len(short_desc)}')
                print(f'  short_description empty: {short_desc == ""}')
        
        # 2. Count schemas with NLLB prefix vs clean
        r = await db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN (translated_content->>'name') LIKE '[NLLB-%' THEN 1 END) as names_with_prefix,
                COUNT(CASE WHEN (translated_content->>'short_description') = '' THEN 1 END) as empty_short_desc,
                COUNT(CASE WHEN (translated_content->>'name') NOT LIKE '[NLLB-%' THEN 1 END) as clean_names
            FROM scheme_translations
            WHERE language_code = 'hi'
        """))
        print('\n=== HI TRANSLATION QUALITY ===')
        row = r.fetchone()
        print(f'  total={row[0]}, names_with_prefix={row[1]}, clean_names={row[3]}, empty_short_desc={row[2]}')

        # 3. Sample API test - test translation injection works at Python level
        from app.services.scheme_service import SchemeService
        from app.repositories.translation_repository import TranslationRepository
        from app.models.enums import LanguageEnum
        
        tr = TranslationRepository(db)
        # Get first translated scheme_id
        r2 = await db.execute(text("SELECT scheme_id FROM scheme_translations WHERE language_code = 'hi' LIMIT 1"))
        scheme_id = r2.scalar()
        print(f'\n=== TESTING TRANSLATION LOOKUP ===')
        print(f'Testing scheme_id: {str(scheme_id)[:8]}')
        
        # Directly test the repository
        import uuid
        trans = await tr.get_by_scheme_and_lang(uuid.UUID(str(scheme_id)), 'hi', only_published=True)
        if trans:
            print(f'  Translation found: id={str(trans.id)[:8]}, published={trans.is_published}, status={trans.status}')
            content = trans.translated_content
            print(f'  Content keys: {list(content.keys())}')
            name = content.get('name', '')
            print(f'  name has_nllb_prefix: {name.startswith("[NLLB-")}')
        else:
            print('  NO TRANSLATION FOUND - get_by_scheme_and_lang returned None!')
        
        # 4. Check valid_langs enum check
        valid_langs = [l.value for l in LanguageEnum]
        print(f'\n=== VALID LANGS CHECK ===')
        print(f'  LanguageEnum values: {valid_langs}')
        print(f'  "hi" in valid_langs: {"hi" in valid_langs}')
        print(f'  "ta" in valid_langs: {"ta" in valid_langs}')

asyncio.run(audit())
