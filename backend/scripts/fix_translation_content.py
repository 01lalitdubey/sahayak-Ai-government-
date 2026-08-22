"""
Fix Translation Content — Sahayak AI
======================================
Strips the [NLLB-200 xx_Xxx]: prefix from all translated_content fields.
The NLLB engine was incorrectly prepending its model tag to every translation.
This script cleans ALL 1200 translation records in-place.
"""
import asyncio
import re
import sys
sys.path.insert(0, '.')

# Pattern: [NLLB-200 hin_Deva]: or [NLLB-200 tam_Taml]: etc.
NLLB_PREFIX_PATTERN = re.compile(r'^\[NLLB-200[^\]]*\]:\s*', re.IGNORECASE)

def strip_prefix(text: str) -> str:
    """Remove [NLLB-200 xx_Xxx]: prefix from translated text."""
    if not text:
        return text
    return NLLB_PREFIX_PATTERN.sub('', text.strip())

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text, select
    from app.models.translation import SchemeTranslation
    
    async with AsyncSessionLocal() as db:
        # Load all translations
        result = await db.execute(select(SchemeTranslation))
        translations = result.scalars().all()
        
        print(f'Loaded {len(translations)} translations')
        
        fixed_count = 0
        for t in translations:
            if not t.translated_content:
                continue
            
            content = dict(t.translated_content)
            changed = False
            
            # Strip prefix from all text fields
            for field in ['name', 'short_description', 'full_description', 'benefits',
                          'eligibility', 'application_process', 'required_documents', 'faq']:
                if field in content and isinstance(content[field], str):
                    original = content[field]
                    cleaned = strip_prefix(original)
                    if cleaned != original:
                        content[field] = cleaned
                        changed = True
            
            if changed:
                t.translated_content = content
                fixed_count += 1
        
        if fixed_count > 0:
            await db.commit()
            print(f'Fixed {fixed_count} translations (stripped NLLB prefix)')
        else:
            print('No translations needed fixing')
        
        # Verify
        result2 = await db.execute(text("""
            SELECT language_code, COUNT(*) 
            FROM scheme_translations 
            WHERE (translated_content->>'name') LIKE '[NLLB-%'
            GROUP BY language_code
        """))
        rows = result2.fetchall()
        if rows:
            print(f'WARNING: Still {len(rows)} languages with NLLB prefix!')
        else:
            print('SUCCESS: No more NLLB prefixes in database')

if __name__ == '__main__':
    asyncio.run(main())
