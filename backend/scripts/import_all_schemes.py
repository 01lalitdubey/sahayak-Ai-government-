"""
import_all_schemes.py — Sahayak AI
=====================================
Downloads ALL ~4693 schemes from the HuggingFace dataset
smartduketech/indian-government-schemes-2025, normalises them via the
existing HuggingFaceNormalizer, and bulk-imports into PostgreSQL via
the existing SchemeImporter with full duplicate detection.

Run from the backend/ directory:
    .venv\\Scripts\\python.exe scripts/import_all_schemes.py

Steps:
  1. Download all pages (length=100, offset=0,100,200,...)
  2. Normalise every record
  3. Import in batches of 100
  4. Full import report
  5. DB verification queries
  6. Duplicate check
  7. API spot-checks
"""

import asyncio
import io
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Make app package importable ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.database import AsyncSessionLocal
from app.government_data.importers.import_statistics import ImportStats
from app.government_data.importers.scheme_importer import SchemeImporter
from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer

# ── Configuration ─────────────────────────────────────────────────────────
DATASET      = "smartduketech/indian-government-schemes-2025"
HF_BASE_URL  = "https://datasets-server.huggingface.co/rows"
PAGE_SIZE    = 100   # HuggingFace max per request
BATCH_SIZE   = 100   # DB commit batch size
API_BASE     = "http://localhost:8000/api/v1"
DIVIDER      = "=" * 70


def banner(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


# ─────────────────────────────────────────────────────────────────────────
# STEP 1 — Download ALL pages from HuggingFace
# ─────────────────────────────────────────────────────────────────────────
def download_all_pages() -> list[dict]:
    banner("STEP 1 — Downloading ALL records from HuggingFace")
    all_records: list[dict] = []
    offset = 0
    page_num = 0

    while True:
        page_num += 1
        url = (
            f"{HF_BASE_URL}"
            f"?dataset={urllib.parse.quote(DATASET, safe='')}"
            f"&config=default&split=train"
            f"&offset={offset}&length={PAGE_SIZE}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SahayakAI/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"  ✗  Page {page_num} (offset={offset}) FAILED: {exc}")
            print("     Stopping download at last successful page.")
            break

        rows = payload.get("rows", [])
        if not rows:
            print(f"  ✓  Page {page_num} (offset={offset}): 0 rows — END OF DATASET")
            break

        records = [r["row"] for r in rows]
        all_records.extend(records)
        print(
            f"  Page {page_num:3d} | offset={offset:5d} | "
            f"page_rows={len(records):3d} | running_total={len(all_records):5d}"
        )

        if len(rows) < PAGE_SIZE:
            # Last page — fewer rows than requested means we're at the end
            print(f"  ✓  Last page reached (returned {len(rows)} < {PAGE_SIZE})")
            break

        offset += PAGE_SIZE

    print(f"\n  ✓  Total downloaded = {len(all_records)}")
    return all_records


# ─────────────────────────────────────────────────────────────────────────
# STEP 2 — Normalise every record
# ─────────────────────────────────────────────────────────────────────────
def normalise_records(records: list[dict]) -> tuple[list, int, list[str]]:
    banner("STEP 2 — Normalising with HuggingFaceNormalizer")
    normalizer = HuggingFaceNormalizer(source_dataset=DATASET)
    valid: list = []
    failed = 0
    warnings: list[str] = []

    for i, rec in enumerate(records, 1):
        result = normalizer.normalize(rec)
        if result.success and result.scheme:
            valid.append(result.scheme)
            if result.warnings:
                for w in result.warnings:
                    warnings.append(f"[{i}] {w}")
        else:
            failed += 1
            errs = "; ".join(e.reason for e in result.errors) if result.errors else "unknown"
            warnings.append(f"[{i}] FAILED: {errs}")
            if failed <= 20:  # print first 20 failures
                print(f"  ✗  [{i:04d}] {errs[:80]}")

    print(f"\n  ✓  Successfully normalised = {len(valid)}")
    print(f"  ✗  Failed normalisation    = {failed}")
    if warnings:
        print(f"  ⚠   Warnings               = {len(warnings)}")

    return valid, failed, warnings


# ─────────────────────────────────────────────────────────────────────────
# STEP 3 — Import in batches
# ─────────────────────────────────────────────────────────────────────────
async def import_in_batches(valid_schemes: list, batch_size: int = BATCH_SIZE) -> ImportStats:
    banner("STEP 3 — Importing into PostgreSQL (batched)")
    stats = ImportStats()
    total = len(valid_schemes)
    num_batches = (total + batch_size - 1) // batch_size
    t_start = time.perf_counter()

    for b_idx in range(num_batches):
        batch_start = b_idx * batch_size
        batch_end   = min(batch_start + batch_size, total)
        batch       = valid_schemes[batch_start:batch_end]

        async with AsyncSessionLocal() as session:
            importer = SchemeImporter(session)
            await importer.import_batch(batch, stats, dry_run=False)

        elapsed = time.perf_counter() - t_start
        rate = (batch_end / elapsed) if elapsed > 0 else 0
        print(
            f"  Batch {b_idx+1:3d}/{num_batches} "
            f"| rows {batch_start+1:5d}–{batch_end:5d}/{total} "
            f"| created={stats.created:5d} updated={stats.updated:4d} "
            f"skipped={stats.skipped:4d} failed={stats.failed:3d} "
            f"| {rate:5.1f} rec/s"
        )

    elapsed_total = time.perf_counter() - t_start
    print(f"\n  ✓  Import complete in {elapsed_total:.1f}s")
    print(f"  ✓  Created  = {stats.created}")
    print(f"  ✓  Updated  = {stats.updated}")
    print(f"  ✓  Skipped  = {stats.skipped}")
    print(f"  ✗  Failed   = {stats.failed}")

    if stats.errors:
        print(f"\n  First {min(10, len(stats.errors))} errors:")
        for err in stats.errors[:10]:
            print(f"    - {err[:100]}")

    return stats, elapsed_total


# ─────────────────────────────────────────────────────────────────────────
# STEP 5 — Verify DB
# ─────────────────────────────────────────────────────────────────────────
async def verify_database() -> None:
    banner("STEP 5 — Database Verification")
    async with AsyncSessionLocal() as db:

        # Total count
        r = await db.execute(text("SELECT COUNT(*) FROM schemes"))
        total = r.scalar_one()
        print(f"\n  SELECT COUNT(*) FROM schemes  =  {total}")

        # Sample rows
        print("\n  Sample rows (name | scheme_code | category | state | ministry):")
        print(f"  {'-'*100}")
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
            FROM schemes
            GROUP BY category
            ORDER BY cnt DESC
        """))
        for row in r.fetchall():
            print(f"    {(row.cat or 'NULL'):<25} : {row.cnt:5d}")

        # State distribution (top 20)
        print("\n  State distribution (top 20):")
        r = await db.execute(text("""
            SELECT COALESCE(state, 'All India / NULL') AS st, COUNT(*) AS cnt
            FROM schemes
            GROUP BY state
            ORDER BY cnt DESC
            LIMIT 20
        """))
        for row in r.fetchall():
            print(f"    {(row.st or 'NULL'):<30} : {row.cnt:5d}")

        # Ministry distribution (top 20)
        print("\n  Ministry distribution (top 20):")
        r = await db.execute(text("""
            SELECT COALESCE(ministry, 'NULL') AS min, COUNT(*) AS cnt
            FROM schemes
            GROUP BY ministry
            ORDER BY cnt DESC
            LIMIT 20
        """))
        for row in r.fetchall():
            print(f"    {(row.min or 'NULL')[:50]:<50} : {row.cnt:5d}")


# ─────────────────────────────────────────────────────────────────────────
# STEP 6 — Duplicate check
# ─────────────────────────────────────────────────────────────────────────
async def check_duplicates() -> int:
    banner("STEP 6 — Duplicate scheme_code Check")
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
        print(f"  ✗  {len(dupes)} duplicate scheme_code values found:")
        for row in dupes[:20]:
            print(f"    {row.scheme_code} — {row.cnt} copies")
    else:
        print("  ✓  0 duplicate scheme_code values — CLEAN")
    return len(dupes)


# ─────────────────────────────────────────────────────────────────────────
# STEP 7 — Verify backend APIs
# ─────────────────────────────────────────────────────────────────────────
async def verify_apis() -> None:
    banner("STEP 7 — Backend API Verification")

    async with AsyncSessionLocal() as db:
        r = await db.execute(
            text("SELECT scheme_code FROM schemes WHERE is_active=true LIMIT 1")
        )
        row = r.fetchone()
        sample_code = row[0] if row else None

    endpoints = [
        f"{API_BASE}/schemes?page=1&page_size=20",
        f"{API_BASE}/schemes/categories",
        f"{API_BASE}/schemes/states",
        f"{API_BASE}/schemes/featured",
        f"{API_BASE}/schemes/recent",
    ]
    if sample_code:
        endpoints.append(f"{API_BASE}/schemes/code/{urllib.parse.quote(sample_code)}")

    all_ok = True
    for url in endpoints:
        short = url.replace(API_BASE, "")
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                body   = json.loads(resp.read().decode("utf-8"))
                extra  = ""
                if "meta" in body:
                    extra = f" | total={body['meta'].get('total', '?')}"
                elif isinstance(body.get("data"), list):
                    extra = f" | count={len(body['data'])}"
                print(f"  ✓  {status}  GET {short}{extra}")
        except Exception as exc:
            print(f"  ✗  FAIL  GET {short}  — {exc}")
            all_ok = False

    if all_ok:
        print("\n  ✓  All API endpoints returned HTTP 200")
    else:
        print("\n  ✗  Some API endpoints failed — is backend running on port 8000?")


# ─────────────────────────────────────────────────────────────────────────
# STEP 9 — Performance metrics
# ─────────────────────────────────────────────────────────────────────────
async def measure_api_perf() -> None:
    banner("STEP 9 — API Performance Metrics")
    endpoints = [
        (f"{API_BASE}/schemes?page=1&page_size=20", "Scheme list (page 1)"),
        (f"{API_BASE}/schemes/featured",             "Featured schemes"),
        (f"{API_BASE}/schemes/categories",           "Categories"),
    ]
    for url, label in endpoints:
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
            ms = (time.perf_counter() - t0) * 1000
            print(f"  {label:<35} : {ms:7.1f} ms")
        except Exception as exc:
            print(f"  {label:<35} : FAILED — {exc}")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
async def main() -> None:
    print("\n[START] Sahayak AI -- Full HuggingFace Dataset Import")
    print("=" * 70)
    print(f"   Dataset : {DATASET}")
    print(f"   API URL : https://datasets-server.huggingface.co/rows")
    print(f"   Target  : ~4693 schemes")
    print(f"   Batch   : {BATCH_SIZE} records per DB transaction")
    script_start = time.perf_counter()

    # STEP 1 — Download
    records = download_all_pages()
    if not records:
        print("\n✗  No records downloaded. Aborting.")
        sys.exit(1)

    # STEP 2 — Normalise
    valid_schemes, failed_norm, warnings = normalise_records(records)
    if not valid_schemes:
        print("\n✗  No valid schemes after normalisation. Aborting.")
        sys.exit(1)

    # STEP 3 — Import
    stats, import_duration = await import_in_batches(valid_schemes)

    # STEP 4 — Report
    banner("STEP 4 — Import Report")
    total_script = time.perf_counter() - script_start
    rate = len(records) / import_duration if import_duration > 0 else 0
    print(f"  Downloaded          = {len(records)}")
    print(f"  Normalised OK       = {len(valid_schemes)}")
    print(f"  Normalised FAILED   = {failed_norm}")
    print(f"  Created             = {stats.created}")
    print(f"  Updated             = {stats.updated}")
    print(f"  Skipped             = {stats.skipped}")
    print(f"  Failed (DB)         = {stats.failed}")
    print(f"  Import duration     = {import_duration:.1f}s")
    print(f"  Throughput          = {rate:.1f} records/s")
    print(f"  Total script time   = {total_script:.1f}s")

    # STEP 5 — DB verification
    await verify_database()

    # STEP 6 — Duplicate check
    dupe_count = await check_duplicates()

    # STEP 7 — API verification
    await verify_apis()

    # STEP 9 — Performance
    await measure_api_perf()

    # ── FINAL REPORT ──────────────────────────────────────────────────────
    banner("FINAL REPORT")
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT COUNT(*) FROM schemes"))
        db_total = r.scalar_one()

    print(f"""
  1. Total downloaded records  : {len(records)}
  2. Total imported (created)  : {stats.created}
  3. Total updated             : {stats.updated}
  4. Total skipped             : {stats.skipped}
  5. Total failed              : {stats.failed + failed_norm}
  6. DB total (COUNT(*))       : {db_total}
  7. Duplicate scheme_codes    : {dupe_count}
  8. Import throughput         : {rate:.1f} rec/s
  9. Import duration           : {import_duration:.1f}s

  SUCCESS CRITERIA:
  {'✓' if db_total >= 4000   else '✗'}  ~4693 schemes in PostgreSQL   (actual: {db_total})
  {'✓' if dupe_count == 0    else '✗'}  No duplicate scheme_code values
  {'✓' if stats.failed < 50  else '✗'}  Failed imports < 50

  Frontend URLs:
    http://localhost:3000/schemes
    http://localhost:3001/schemes

  API Docs:
    http://localhost:8000/docs
""")

    if warnings[:5]:
        print("  First normalisation warnings:")
        for w in warnings[:5]:
            print(f"    {w[:100]}")


if __name__ == "__main__":
    asyncio.run(main())
