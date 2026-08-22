import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Check an API call with lang=hi
        r = await client.get('http://127.0.0.1:8000/api/v1/schemes?lang=hi&page_size=2')
        print("GET /schemes?lang=hi")
        print("Status:", r.status_code)
        
        data = r.json().get('data', [])
        for item in data:
            print("Scheme ID:", item.get('id'))
            print("Name:", item.get('name'))
            print("Code:", item.get('scheme_code'))

if __name__ == "__main__":
    asyncio.run(main())
