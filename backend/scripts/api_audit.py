import httpx
import json
import asyncio

async def test_apis():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("Testing GET /schemes?lang=hi")
        r1 = await client.get(f"{base_url}/schemes?lang=hi")
        data = r1.json()
        print(f"Status: {r1.status_code}")
        if data.get('data') and len(data['data']) > 0:
            print(f"First Scheme Name: {data['data'][0].get('name')}")
        
        print("\nTesting GET /schemes/featured?lang=ta")
        r2 = await client.get(f"{base_url}/schemes/featured?lang=ta")
        data2 = r2.json()
        print(f"Status: {r2.status_code}")
        if data2.get('data') and len(data2['data']) > 0:
            print(f"First Scheme Name: {data2['data'][0].get('name')}")

if __name__ == "__main__":
    asyncio.run(test_apis())
