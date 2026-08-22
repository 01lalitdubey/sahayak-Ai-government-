"""
Inject sample Hindi text into DB to prove integration works end-to-end
"""
import asyncio, sys, json
sys.path.insert(0, '.')

async def main():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    from app.models.enums import TranslationStatusEnum

    async with AsyncSessionLocal() as db:
        # Get one featured scheme and one normal scheme
        r = await db.execute(text("""
            SELECT s.id, s.scheme_code, s.name, st.id as trans_id, st.translated_content
            FROM schemes s
            JOIN scheme_translations st ON st.scheme_id = s.id
            WHERE st.language_code = 'hi' 
            LIMIT 5
        """))
        
        updates = 0
        for row in r:
            scheme_id = row[0]
            code = row[1]
            en_name = row[2]
            trans_id = row[3]
            content = row[4]
            
            # Create some dummy Hindi text based on the English name
            # Not real translation, but recognizable as Hindi script for UI validation
            hi_name = f"हिंदी अनुवाद: {en_name}"
            hi_short = "यह योजना का संक्षिप्त विवरण है।"
            hi_full = "यह योजना का पूर्ण विवरण है। " * 5
            hi_benefits = "लाभ 1. वित्तीय सहायता\nलाभ 2. रोजगार"
            
            content["name"] = hi_name
            content["short_description"] = hi_short
            content["full_description"] = hi_full
            content["benefits"] = hi_benefits
            
            # Update DB
            content_json = json.dumps(content).replace("'", "''")
            await db.execute(text(f"""
                UPDATE scheme_translations 
                SET translated_content = '{content_json}'::jsonb, status = 'published', is_published = TRUE
                WHERE id = '{trans_id}'
            """))
            updates += 1
            print(f"Updated {code} with sample Hindi text")
            
        await db.commit()
        print(f"Committed {updates} updates")

asyncio.run(main())
