import asyncio
import asyncpg
import json
import re

async def main():
    c = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost/sahayak_db')
    
    total = await c.fetchval('SELECT COUNT(*) FROM scheme_translations')
    print(f"Total Translations: {total}")
    
    by_lang = await c.fetch('SELECT language_code, COUNT(*) FROM scheme_translations GROUP BY language_code')
    print("By Language:")
    for row in by_lang:
        print(f"  {row['language_code']}: {row['count']}")
        
    await c.close()

asyncio.run(main())
