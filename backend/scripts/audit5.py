import asyncio
import sys
sys.path.insert(0, '.')

async def audit():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as db:
        # Get a scheme_code that HAS a translation
        r = await db.execute(text("""
            SELECT s.scheme_code, s.name, st.language_code
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            WHERE st.language_code = 'hi' AND s.is_active = true
            LIMIT 5
        """))
        print('=== SCHEME CODES WITH HI TRANSLATIONS ===')
        codes = []
        for row in r:
            codes.append(row[0])
            print(f'  code={row[0]}, name={row[1][:60]}')
        
        # Directly test the inject_translation method
        from app.services.scheme_service import SchemeService
        from app.repositories.scheme_repository import SchemeRepository
        
        svc = SchemeService(db)
        repo = SchemeRepository(db)
        
        if codes:
            scheme = await repo.get_by_code(codes[0])
            if scheme:
                original_name = scheme.name
                print(f'\n=== TESTING inject_translation ===')
                print(f'Before: name={scheme.name[:60]}')
                
                await svc._inject_translation(scheme, 'hi')
                
                print(f'After:  name={scheme.name[:60]}')
                print(f'Changed: {scheme.name != original_name}')
                
                # Also test bulk
                scheme2 = await repo.get_by_code(codes[0])
                orig_name2 = scheme2.name
                await svc._inject_translations_bulk([scheme2], 'hi')
                print(f'\nBulk inject changed: {scheme2.name != orig_name2}')

asyncio.run(audit())
