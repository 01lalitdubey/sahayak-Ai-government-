"""
verify_import.py — Sahayak AI
==============================
Verification-only script. Runs Steps 5-10 without re-downloading.
Run from the backend/ directory:
    .venv\\Scripts\\python.exe scripts/verify_import.py
"""

import asyncio
import io
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database.database import AsyncSessionLocal

API_BASE = "http://localhost:8000/api/v1"
DIV = "=" * 70

def banner(title: str) -> None:
    print(f"\n{DIV}\n  {title}\n{DIV}")


async def verify_all() -> None:
    print("\n[VERIFY] Sahayak AI -- Post-Import Verification")
    print(DIV)

    # ── STEP 5: DB Verification ───────────────────────────────────────────
    banner("STEP 5 -- Database Verification")
    async with AsyncSessionLocal() as db:

        r = await db.execute(text("SELECT COUNT(*) FROM schemes"))
        total = r.scalar_one()
        r2 = await db.execute(text("SELECT COUNT(*) FROM schemes WHERE is_active=true"))
        active = r2.scalar_one()
        print(f"\n  Total schemes (COUNT*)       = {total}")
        print(f"  Active schemes               = {active}")
        print(f"  Inactive schemes             = {total - active}")

        # Sample 20 most-recently imported
        print("\n  Sample rows (name | scheme_code | category | state | ministry):")
        print(f"  {'-'*105}")
        r = await db.execute(text("""
            SELECT name, scheme_code, category, state, ministry
            FROM schemes
            ORDER BY created_at DESC
            LIMIT 20
        """))
        for row in r.fetchall():
            name     = (row.name or "")[:40]
            code     = (row.scheme_code or "")[:20]
            cat      = (str(row.category) if row.category else "")[:15]
            state    = (row.state or "All India")[:15]
            ministry = (row.ministry or "")[:25]
            print(f"  {name:<40} | {code:<20} | {cat:<15} | {state:<15} | {ministry}")

        # Category distribution
        print("\n  Category distribution:")
        r = await db.execute(text("""
            SELECT COALESCE(category::text, 'NULL') AS cat, COUNT(*) AS cnt
            FROM schemes GROUP BY category ORDER BY cnt DESC
        """))
        for row in r.fetchall():
            print(f"    {(row.cat or 'NULL'):<25} : {row.cnt:5d}")

        # State distribution
        print("\n  State distribution (top 20):")
        r = await db.execute(text("""
            SELECT COALESCE(state, 'All India / NULL') AS st, COUNT(*) AS cnt
            FROM schemes GROUP BY state ORDER BY cnt DESC LIMIT 20
        """))
        for row in r.fetchall():
            print(f"    {(row.st or 'NULL'):<30} : {row.cnt:5d}")

        # Ministry distribution
        print("\n  Ministry distribution (top 20):")
        r = await db.execute(text("""
            SELECT COALESCE(ministry, 'NULL') AS mn, COUNT(*) AS cnt
            FROM schemes GROUP BY ministry ORDER BY cnt DESC LIMIT 20
        """))
        for row in r.fetchall():
            print(f"    {(row.mn or 'NULL')[:50]:<50} : {row.cnt:5d}")

    # ── STEP 6: Duplicate Check ───────────────────────────────────────────
    banner("STEP 6 -- Duplicate scheme_code Check")
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT scheme_code, COUNT(*) AS cnt
            FROM schemes
            GROUP BY scheme_code
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """))
        dupes = r.fetchall()

    if dupes:
        print(f"  FAIL  {len(dupes)} duplicate scheme_code values found:")
        for row in dupes[:20]:
            print(f"    {row.scheme_code} -- {row.cnt} copies")
        dupe_count = len(dupes)
    else:
        print("  OK  0 duplicate scheme_code values -- CLEAN")
        dupe_count = 0

    # ── STEP 7: API Verification ──────────────────────────────────────────
    banner("STEP 7 -- Backend API Verification")

    # get a real scheme_code for the detail test
    sample_code: str | None = None
    async with AsyncSessionLocal() as db:
        r = await db.execute(
            text("SELECT scheme_code FROM schemes WHERE is_active=true ORDER BY created_at DESC LIMIT 1")
        )
        row = r.fetchone()
        sample_code = row[0] if row else None

    endpoints = [
        (f"{API_BASE}/schemes?page=1&page_size=20",        "/schemes?page=1&page_size=20"),
        (f"{API_BASE}/schemes?page=2&page_size=20",        "/schemes?page=2&page_size=20"),
        (f"{API_BASE}/schemes/categories",                  "/schemes/categories"),
        (f"{API_BASE}/schemes/states",                      "/schemes/states"),
        (f"{API_BASE}/schemes/featured",                    "/schemes/featured"),
        (f"{API_BASE}/schemes/recent",                      "/schemes/recent"),
        (f"{API_BASE}/schemes?query=education",             "/schemes?query=education"),
        (f"{API_BASE}/schemes?category=agriculture",        "/schemes?category=agriculture"),
    ]
    if sample_code:
        endpoints.append((
            f"{API_BASE}/schemes/code/{urllib.parse.quote(sample_code)}",
            f"/schemes/code/{sample_code[:30]}"
        ))

    all_ok = True
    for url, label in endpoints:
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                body   = json.loads(resp.read().decode("utf-8"))
            ms = (time.perf_counter() - t0) * 1000
            extra = ""
            if "meta" in body:
                meta = body["meta"]
                extra = f" | total={meta.get('total','?')} pages={meta.get('pages','?')}"
            elif isinstance(body.get("data"), list):
                extra = f" | count={len(body['data'])}"
            elif isinstance(body.get("data"), dict):
                extra = f" | name={body['data'].get('name','?')[:40]}"
            print(f"  OK  {status}  {label:<45}  {ms:6.1f}ms{extra}")
        except Exception as exc:
            print(f"  FAIL       {label:<45}  -- {exc}")
            all_ok = False

    if all_ok:
        print("\n  All API endpoints returned HTTP 200")
    else:
        print("\n  Some API endpoints failed -- ensure backend is running on :8000")

    # ── STEP 9: Performance ───────────────────────────────────────────────
    banner("STEP 9 -- API Performance Metrics")
    perf_endpoints = [
        (f"{API_BASE}/schemes?page=1&page_size=20",   "Scheme list p1 (20 items)"),
        (f"{API_BASE}/schemes?page=10&page_size=20",  "Scheme list p10 (deep page)"),
        (f"{API_BASE}/schemes?query=education",        "Search: education"),
        (f"{API_BASE}/schemes/featured",               "Featured schemes"),
        (f"{API_BASE}/schemes/categories",             "Categories"),
        (f"{API_BASE}/schemes/states",                 "States"),
    ]
    for url, label in perf_endpoints:
        times = []
        for _ in range(3):  # 3 samples per endpoint
            t0 = time.perf_counter()
            try:
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp.read()
                times.append((time.perf_counter() - t0) * 1000)
            except Exception as exc:
                times.append(-1)
        valid = [t for t in times if t >= 0]
        if valid:
            avg = sum(valid) / len(valid)
            mn  = min(valid)
            print(f"  {label:<35} avg={avg:6.1f}ms  min={mn:6.1f}ms")
        else:
            print(f"  {label:<35} FAILED (backend not reachable)")

    # ── STEP 10: Existing tests ───────────────────────────────────────────
    banner("STEP 10 -- Existing Features Verification")
    print("  (Run: .venv\\Scripts\\python.exe -m pytest tests/ -q  to verify 639 tests)")

    # ── FINAL REPORT ─────────────────────────────────────────────────────
    banner("FINAL REPORT")
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT COUNT(*) FROM schemes"))
        db_total = r.scalar_one()
        r = await db.execute(text("SELECT COUNT(*) FROM schemes WHERE is_active=true"))
        db_active = r.scalar_one()

    criteria_total = db_total >= 3000   # dataset after dedup may be ~3599
    criteria_dupes = dupe_count == 0
    criteria_api   = all_ok

    print(f"""
  1. Total downloaded records   : (from prior run)
  2. Total schemes in DB        : {db_total}
  3. Active schemes             : {db_active}
  4. Duplicate scheme_codes     : {dupe_count}
  5. API endpoints all 200      : {'YES' if all_ok else 'NO'}

  SUCCESS CRITERIA:
  {'OK' if criteria_total else 'FAIL'}  Schemes in PostgreSQL >= 3000     (actual: {db_total})
  {'OK' if criteria_dupes else 'FAIL'}  No duplicate scheme_code values
  {'OK' if criteria_api   else 'FAIL'}  All API endpoints HTTP 200

  Frontend URLs to verify manually:
    http://localhost:3000/schemes
    http://localhost:3001/schemes

  Detail page test:
    http://localhost:3000/schemes/{urllib.parse.quote(sample_code or 'IRA-WRFLSNCS')}
    http://localhost:3001/schemes/{urllib.parse.quote(sample_code or 'IRA-WRFLSNCS')}

  API Docs:
    http://localhost:8000/docs
""")


if __name__ == "__main__":
    asyncio.run(verify_all())
