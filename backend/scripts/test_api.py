"""Test public API endpoint."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json

def test_url(url, label):
    print(f"\n--- {label} ---")
    print(f"URL: {url}")
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        print(f"STATUS: 200 OK")
        meta = data.get("meta", {})
        items = data.get("data", [])
        print(f"meta.total: {meta.get('total')}")
        print(f"meta.page: {meta.get('page')}")
        print(f"meta.page_size: {meta.get('page_size')}")
        print(f"meta.total_pages: {meta.get('total_pages')}")
        print(f"data (items) count: {len(items)}")
        print(f"success: {data.get('success')}")
        if items:
            first = items[0]
            print(f"First item is_active: {first.get('is_active')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"HTTP ERROR {e.code}: {body[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")

test_url("http://localhost:8000/api/v1/schemes", "GET /api/v1/schemes (no params)")
test_url("http://localhost:8000/api/v1/schemes?page=1&page_size=20&sort=newest", "GET with defaults")
test_url("http://localhost:8000/api/v1/schemes?lang=en", "GET ?lang=en")
test_url("http://localhost:8000/api/v1/schemes?page=1&page_size=5", "GET page=1&page_size=5")
