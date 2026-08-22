"""
seed_10_schemes.py — Sahayak AI
=================================
Downloads the first 10 records from the HuggingFace dataset
smartduketech/indian-government-schemes-2025, normalises them using
the existing HuggingFaceNormalizer, inserts them into PostgreSQL via
the existing SchemeImporter (with full duplicate detection), and
verifies the result with a direct SQL query.

Run from the backend/ directory:
    .venv\Scripts\python.exe scripts/seed_10_schemes.py
"""

import asyncio
import json
import sys
import urllib.request
from pathlib import Path

# ── Make sure app package is importable ───────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.database import AsyncSessionLocal
from app.government_data.importers.import_statistics import ImportStats
from app.government_data.importers.scheme_importer import SchemeImporter
from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer


# ── Constants ─────────────────────────────────────────────────────────────
HF_ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=smartduketech%2Findian-government-schemes-2025"
    "&config=default&split=train&offset=0&length=10"
)
DATASET_ID = "smartduketech/indian-government-schemes-2025"
DIVIDER = "=" * 60


def _banner(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


# ─────────────────────────────────────────────────────────────────────────
# STEP 1 & 2 — Download and extract rows
# ─────────────────────────────────────────────────────────────────────────
def fetch_10_rows() -> list[dict]:
    _banner("STEP 1 — Downloading 10 records from HuggingFace")
    req = urllib.request.Request(
        HF_ROWS_URL,
        headers={"User-Agent": "SahayakAI/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    rows = payload.get("rows", [])
    records = [r["row"] for r in rows]

    print(f"✓  Downloaded = {len(records)}")

    _banner("STEP 2 — Extracting row objects")
    print(f"✓  Parsed objects = {len(records)}")

    return records


# ─────────────────────────────────────────────────────────────────────────
# STEP 3 — Normalize
# ─────────────────────────────────────────────────────────────────────────
def normalize_records(records: list[dict]):
    _banner("STEP 3 — Normalising with HuggingFaceNormalizer")
    normalizer = HuggingFaceNormalizer(source_dataset=DATASET_ID)

    valid_schemes = []
    for i, rec in enumerate(records, 1):
        result = normalizer.normalize(rec)
        s = result.scheme
        if result.success and s:
            valid_schemes.append(s)
            print(
                f"  [{i:02d}] ✓  Name      : {(s.name or '')[:60]}\n"
                f"           Category  : {s.category}\n"
                f"           State     : {s.state}\n"
                f"           Code      : {s.scheme_code}\n"
            )
        else:
            errs = ", ".join(e.reason for e in result.errors)
            print(f"  [{i:02d}] ✗  FAILED    : {errs}")

    print(f"\n✓  Successfully normalised = {len(valid_schemes)} / {len(records)}")
    return valid_schemes


# ─────────────────────────────────────────────────────────────────────────
# STEP 4 — Insert into PostgreSQL
# ─────────────────────────────────────────────────────────────────────────
async def insert_schemes(valid_schemes) -> ImportStats:
    _banner("STEP 4 — Inserting schemes into PostgreSQL")
    stats = ImportStats()
    async with AsyncSessionLocal() as session:
        importer = SchemeImporter(session)
        actions = await importer.import_batch(valid_schemes, stats, dry_run=False)

    print(f"  Created  = {stats.created}")
    print(f"  Updated  = {stats.updated}")
    print(f"  Skipped  = {stats.skipped}")
    print(f"  Failed   = {stats.failed}")
    print(f"  Actions  = {actions}")
    print(f"\n✓  Transaction committed.")
    return stats


# ─────────────────────────────────────────────────────────────────────────
# STEP 5 — COUNT(*) verification
# ─────────────────────────────────────────────────────────────────────────
async def verify_count() -> int:
    _banner("STEP 5 — SELECT COUNT(*) FROM schemes")
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM schemes"))
        count = result.scalar_one()
    print(f"  COUNT(*) = {count}")
    return count


# ─────────────────────────────────────────────────────────────────────────
# STEP 6 — Print first 10 rows from DB
# ─────────────────────────────────────────────────────────────────────────
async def print_db_rows() -> None:
    _banner("STEP 6 — SELECT name, category, state, scheme_code FROM schemes LIMIT 10")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT name, category, state, scheme_code FROM schemes LIMIT 10")
        )
        rows = result.fetchall()

    if not rows:
        print("  ⚠  No rows found in schemes table!")
        return

    for i, (name, category, state, code) in enumerate(rows, 1):
        cat_str = str(category) if category is not None else 'None'
        print(
            f"  [{i:02d}] {(name or '')[:50]:<50} | "
            f"{cat_str:<20} | "
            f"{(state or 'None'):<20} | "
            f"{(code or 'None')}"
        )


# ─────────────────────────────────────────────────────────────────────────
# STEP 7 — Call GET /api/v1/schemes via HTTP
# ─────────────────────────────────────────────────────────────────────────
def call_api() -> None:
    _banner("STEP 7 — GET /api/v1/schemes?page=1&page_size=10")
    url = "http://localhost:8000/api/v1/schemes?page=1&page_size=10"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))

        schemes_list = body.get("data", [])
        meta = body.get("meta", {})

        print(f"  HTTP Status = {status}")
        print(f"  Total in meta = {meta.get('total', '?')}")
        print(f"  Returned count = {len(schemes_list)}")

        for i, s in enumerate(schemes_list, 1):
            print(
                f"  [{i:02d}] {(s.get('name',''))[:55]:<55} | "
                f"{s.get('category','?'):<20} | "
                f"{s.get('state','?')}"
            )
        print(f"\n✓  API returned {len(schemes_list)} schemes successfully.")
    except Exception as exc:
        print(f"  ✗  API call failed: {exc}")
        print("     (Is the backend running on port 8000?)")


# ─────────────────────────────────────────────────────────────────────────
# STEP 10 — Re-run import (expect all skipped)
# ─────────────────────────────────────────────────────────────────────────
async def reimport_expect_skip(valid_schemes) -> None:
    _banner("STEP 10 — Re-import (expect all skipped)")
    stats2 = ImportStats()
    async with AsyncSessionLocal() as session:
        importer = SchemeImporter(session)
        await importer.import_batch(valid_schemes, stats2, dry_run=False)

    print(f"  Created  = {stats2.created}  (expected 0)")
    print(f"  Updated  = {stats2.updated}  (expected 0)")
    print(f"  Skipped  = {stats2.skipped}  (expected {len(valid_schemes)})")
    print(f"  Failed   = {stats2.failed}   (expected 0)")
    ok = stats2.created == 0 and stats2.skipped == len(valid_schemes) and stats2.failed == 0
    print(f"\n  {'✓  Duplicate detection PASSED' if ok else '✗  Duplicate detection FAILED'}")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
async def main() -> None:
    print("\n🚀 Sahayak AI — Seed 10 Government Schemes")
    print("============================================")

    # Steps 1–2
    records = fetch_10_rows()

    # Step 3
    valid_schemes = normalize_records(records)

    if not valid_schemes:
        print("\n✗  No valid schemes after normalisation. Aborting.")
        sys.exit(1)

    # Step 4
    stats = await insert_schemes(valid_schemes)

    # Step 5
    count = await verify_count()
    if count == 0:
        print("\n✗  count=0 — something went wrong with the insert!")

    # Step 6
    await print_db_rows()

    # Step 7
    call_api()

    # Step 10
    await reimport_expect_skip(valid_schemes)

    _banner("FINAL SUMMARY")
    print(f"  ✓  Downloaded   = {len(records)}")
    print(f"  ✓  Normalised   = {len(valid_schemes)}")
    print(f"  ✓  DB COUNT(*)  = {count}")
    print(
        f"  {'✓' if stats.created > 0 or stats.skipped > 0 else '?'}"
        f"  Inserted (created + skipped) = {stats.created + stats.skipped}"
    )
    print(f"\n  Frontend URL: http://localhost:3000/schemes")
    print(f"                http://localhost:3001/schemes")
    print("\n  Open either URL in your browser to verify the scheme cards.\n")


if __name__ == "__main__":
    asyncio.run(main())
