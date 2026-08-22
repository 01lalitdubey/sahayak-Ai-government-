"""
Forensic API audit — test all scheme endpoints.
"""
import asyncio
import httpx


BASE = "http://localhost:8000"


async def audit():
    async with httpx.AsyncClient(timeout=30) as client:
        print("=== API FORENSIC AUDIT ===\n")

        # 1. Public schemes endpoint — no params
        r = await client.get(f"{BASE}/api/v1/schemes")
        print(f"GET /api/v1/schemes  → status={r.status_code}")
        body = r.json()
        print(f"  success={body.get('success')}")
        print(f"  total={body.get('meta', {}).get('total')}")
        print(f"  items_count={len(body.get('data', []))}")
        if body.get("data"):
            print(f"  first_item_keys={list(body['data'][0].keys())}")
        print()

        # 2. With page/page_size
        r2 = await client.get(f"{BASE}/api/v1/schemes?page=1&page_size=20")
        b2 = r2.json()
        print(f"GET /api/v1/schemes?page=1&page_size=20  → status={r2.status_code}")
        print(f"  total={b2.get('meta', {}).get('total')}")
        print(f"  items={len(b2.get('data', []))}")
        print()

        # 3. With lang=en
        r3 = await client.get(f"{BASE}/api/v1/schemes?lang=en")
        b3 = r3.json()
        print(f"GET /api/v1/schemes?lang=en  → status={r3.status_code}")
        print(f"  total={b3.get('meta', {}).get('total')}")
        print(f"  items={len(b3.get('data', []))}")
        print()

        # 4. Full raw response for debugging
        r4 = await client.get(f"{BASE}/api/v1/schemes?page=1&page_size=5&sort=newest")
        b4 = r4.json()
        print(f"GET /api/v1/schemes?page=1&page_size=5&sort=newest  → status={r4.status_code}")
        print(f"  meta={b4.get('meta')}")
        print(f"  items={len(b4.get('data', []))}")
        if b4.get("data"):
            print(f"  first_scheme_name={b4['data'][0].get('name', 'N/A')[:60]}")
        print()

        # 5. Featured
        r5 = await client.get(f"{BASE}/api/v1/schemes/featured")
        b5 = r5.json()
        print(f"GET /api/v1/schemes/featured  → status={r5.status_code}")
        print(f"  total={b5.get('meta', {}).get('total')}")
        print()

        # 6. Recent
        r6 = await client.get(f"{BASE}/api/v1/schemes/recent")
        b6 = r6.json()
        print(f"GET /api/v1/schemes/recent  → status={r6.status_code}")
        print(f"  total={b6.get('meta', {}).get('total')}")
        print()

        print("=== API AUDIT COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(audit())
