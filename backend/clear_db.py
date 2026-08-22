import asyncio
import asyncpg

async def main():
    c = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost/sahayak_db')
    await c.execute('TRUNCATE scheme_translations CASCADE;')
    await c.execute('TRUNCATE translation_history CASCADE;')
    await c.close()
    print("DB Cleared!")

asyncio.run(main())
