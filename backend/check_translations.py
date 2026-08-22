import asyncio
import asyncpg
import json

async def main():
    c = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost/sahayak_db')
    rows = await c.fetch("SELECT language_code, translated_content FROM scheme_translations LIMIT 10")
    
    output = []
    for r in rows:
        output.append({
            "lang": r['language_code'],
            "content": r['translated_content']
        })
        
    with open('translations_dump.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    await c.close()

asyncio.run(main())
