import asyncio
import asyncpg
import json

async def main():
    c = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost/sahayak_db')
    print('Total Schemes:', await c.fetchval('SELECT COUNT(*) FROM schemes'))
    print('Total Translations:', await c.fetchval('SELECT COUNT(*) FROM scheme_translations'))
    
    published = await c.fetchval('SELECT COUNT(*) FROM scheme_translations WHERE is_published = TRUE')
    print('Published Translations:', published)
    
    sample = await c.fetch('SELECT language_code, translated_content FROM scheme_translations LIMIT 20')
    print('--- 20 Samples ---')
    for row in sample:
        try:
            # PostgreSQL asyncpg handles JSONB as strings sometimes depending on connection config, or dicts
            content = json.loads(row['translated_content']) if isinstance(row['translated_content'], str) else row['translated_content']
            name = content.get('name', 'N/A')
            print(f"[{row['language_code']}] {name[:50]}")
        except Exception as e:
            print(f"[{row['language_code']}] ERROR parsing JSON: {e}")
    await c.close()

if __name__ == "__main__":
    asyncio.run(main())
