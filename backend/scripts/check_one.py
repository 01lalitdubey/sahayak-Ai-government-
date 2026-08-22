import asyncio
import asyncpg
import json
import httpx

async def main():
    c = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost/sahayak_db')
    sample = await c.fetch("SELECT scheme_id, language_code, translated_content FROM scheme_translations WHERE language_code = 'hi' LIMIT 1")
    
    with open('api_test_results.txt', 'w', encoding='utf-8') as f:
        if sample:
            sid = sample[0]['scheme_id']
            content = sample[0]['translated_content']
            if isinstance(content, str):
                content = json.loads(content)
            name = content.get('name')
            f.write(f'Translated Scheme ID: {sid}\n')
            f.write(f'Hindi Name: {name}\n')
            
            eng = await c.fetch('SELECT name FROM schemes WHERE id = $1', sid)
            f.write(f'English Name: {eng[0]["name"]}\n')
            
            # Test API
            async with httpx.AsyncClient() as client:
                r = await client.get(f'http://127.0.0.1:8000/api/v1/schemes/{sid}?lang=hi')
                f.write(f'API GET /schemes/{sid}?lang=hi\n')
                f.write(f'Status: {r.status_code}\n')
                data = r.json().get('data', {})
                f.write(f'API Returned Name: {data.get("name")}\n')
                
    await c.close()

if __name__ == "__main__":
    asyncio.run(main())
