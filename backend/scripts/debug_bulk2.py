"""Trace _inject_translations_bulk in context of recommendation_service"""
import asyncio
import sys
sys.path.insert(0, '.')

async def debug():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        from app.repositories.scheme_repository import SchemeRepository
        from app.services.scheme_service import SchemeService

        repo = SchemeRepository(db)
        
        # Get a few schemes that have translations
        r = await db.execute(text("""
            SELECT s.id, s.scheme_code, s.name 
            FROM schemes s
            JOIN scheme_translations st ON st.scheme_id = s.id
            WHERE st.language_code = 'hi' AND s.is_active = true
            LIMIT 5
        """))
        rows = r.fetchall()
        
        import uuid
        from app.models.scheme import Scheme
        from sqlalchemy import select
        
        # Load these actual scheme objects
        scheme_ids = [uuid.UUID(str(row[0])) for row in rows]
        
        result = await db.execute(
            select(Scheme).where(Scheme.id.in_(scheme_ids))
        )
        schemes = list(result.scalars().all())
        print(f'Loaded {len(schemes)} scheme objects')
        print(f'First scheme name: {schemes[0].name[:60]}')
        
        # Test _inject_translations_bulk directly
        svc = SchemeService(db)
        original_names = {s.id: s.name for s in schemes}
        
        await svc._inject_translations_bulk(schemes, 'hi')
        
        changed = sum(1 for s in schemes if s.name != original_names[s.id])
        print(f'Names changed after bulk inject: {changed}/{len(schemes)}')
        for s in schemes[:3]:
            print(f'  Before: {original_names[s.id][:60]}')
            print(f'  After:  {s.name[:60]}')
            print()
        
        # Also check: does RecommendationService's usage work?
        # It calls SchemeService(self._repo._db) - _repo is RecommendationRepository
        from app.repositories.recommendation_repository import RecommendationRepository
        rec_repo = RecommendationRepository(db)
        
        schemes2 = await rec_repo.get_all_active_schemes()
        print(f'\nAll active schemes for recommendation: {len(schemes2)}')
        
        # Find which have translations
        hi_ids = set(scheme_ids)
        schemes_with_trans = [s for s in schemes2 if s.id in hi_ids]
        print(f'Of those, have hi translation: {len(schemes_with_trans)}')
        
        # Try the inject
        svc2 = SchemeService(rec_repo._db)
        orig2 = {s.id: s.name for s in schemes_with_trans}
        await svc2._inject_translations_bulk(schemes_with_trans, 'hi')
        changed2 = sum(1 for s in schemes_with_trans if s.name != orig2[s.id])
        print(f'Names changed via rec_repo: {changed2}/{len(schemes_with_trans)}')

asyncio.run(debug())
