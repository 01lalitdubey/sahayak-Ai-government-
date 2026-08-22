import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost:5432/sahayak_db')
    
    for col in ['required_documents', 'application_process']:
        query = "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'schemes' AND column_name = $1"
        exists = await conn.fetchval(query, col)
        print(f'Column {col!r}: exists={bool(exists)}')
    
    await conn.close()

asyncio.run(main())
