"""Deep debug bulk injection failure"""
import asyncio
import sys
sys.path.insert(0, '.')

async def debug():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # Get scheme IDs that have translations
        r = await db.execute(text("""
            SELECT scheme_id FROM scheme_translations WHERE language_code = 'hi' LIMIT 5
        """))
        scheme_ids_raw = [row[0] for row in r]
        print(f'Scheme IDs with hi translations: {[str(s)[:8] for s in scheme_ids_raw]}')
        
        # Test TranslationRepository directly
        import uuid
        from app.repositories.translation_repository import TranslationRepository
        
        tr = TranslationRepository(db)
        scheme_ids = [uuid.UUID(str(s)) for s in scheme_ids_raw]
        
        # Test single lookup
        single = await tr.get_by_scheme_and_lang(scheme_ids[0], 'hi', only_published=True)
        print(f'\nSingle lookup result: {single is not None}')
        if single:
            print(f'  id={str(single.id)[:8]}, name in content: {"name" in single.translated_content}')
        
        # Test bulk lookup
        bulk = await tr.get_by_scheme_ids_and_lang(scheme_ids, 'hi', only_published=True)
        print(f'\nBulk lookup result count: {len(bulk)}')
        if bulk:
            for t in bulk[:2]:
                print(f'  id={str(t.id)[:8]}, scheme_id={str(t.scheme_id)[:8]}')
        else:
            print('  BULK RETURNED EMPTY! This is the bug.')
            
        # Test without only_published
        bulk_any = await tr.get_by_scheme_ids_and_lang(scheme_ids, 'hi', only_published=False)
        print(f'\nBulk lookup (any status) count: {len(bulk_any)}')
        
        # Check if session vs _db is the issue
        print(f'\nTranslationRepository uses: self.session')
        print(f'SchemeRepository uses: self._db')
        
        # The issue: SchemeService creates TranslationRepository(db)
        # where db is an AsyncSession object
        # TranslationRepository uses self.session
        # Let's verify the session is same object
        from app.services.scheme_service import SchemeService
        svc = SchemeService(db)
        print(f'\nSchemeService._trans_repo.session is db: {svc._trans_repo.session is db}')
        print(f'SchemeService._repo._db is db: {svc._repo._db is db}')

asyncio.run(debug())
