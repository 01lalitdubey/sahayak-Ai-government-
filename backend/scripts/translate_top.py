import asyncio
import os
import sys

sys.path.insert(0, ".")
os.environ["PYTHONIOENCODING"] = "utf-8"

async def force_translate_top():
    from app.database.database import AsyncSessionLocal
    from app.models.scheme import Scheme
    from sqlalchemy import select
    from app.services.translation.indictrans2_provider import IndicTrans2Provider
    from scripts.translate_all import upsert_translation
    import hashlib
    import json
    
    print("Initializing IndicTrans2 Provider...")
    provider = IndicTrans2Provider()
    langs = ["hi", "ta", "te", "mr", "gu", "bn", "kn", "ml", "pa", "or", "as"]
    
    async with AsyncSessionLocal() as db:
        # Fetch Top 20 Most Viewed Schemes (the ones shown on default API)
        stmt = select(Scheme).order_by(Scheme.view_count.desc()).limit(20)
        result = await db.execute(stmt)
        schemes = result.scalars().all()
        
        print(f"Force translating {len(schemes)} most viewed schemes...")
        
        for scheme in schemes:
            print(f"Translating Scheme ID: {scheme.id}")
            text_dict = {
                "name": scheme.name or "",
                "short_description": scheme.short_description or "",
                "full_description": scheme.full_description or "",
                "benefits": scheme.benefits or ""
            }
            
            for lang in langs:
                try:
                    translated = await provider.translate_json(text_dict, "en", lang)
                    # Create Checksum
                    hash_input = f"{scheme.id}:{lang}:{json.dumps(translated, sort_keys=True)}"
                    checksum = hashlib.sha256(hash_input.encode()).hexdigest()
                    
                    await upsert_translation(db, scheme.id, lang, translated, checksum)
                    print(f"  [{lang}] Saved")
                except Exception as e:
                    print(f"  [{lang}] Failed to save")
                    
        print("Done!")

if __name__ == "__main__":
    asyncio.run(force_translate_top())
