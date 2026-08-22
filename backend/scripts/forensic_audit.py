"""
Forensic Audit Script — Sahayak AI
Checks DB state and public API.
"""
import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg


async def run():
    conn = await asyncpg.connect(
        'postgresql://sahayak:sahayak_password@localhost:5432/sahayak_db'
    )

    print("=" * 60)
    print("STEP 1 — DATABASE SCHEME COUNTS")
    print("=" * 60)

    total = await conn.fetchval("SELECT COUNT(*) FROM schemes")
    print(f"Total schemes: {total}")

    rows = await conn.fetch(
        "SELECT is_active, COUNT(*) as cnt FROM schemes GROUP BY is_active ORDER BY is_active"
    )
    for r in rows:
        print(f"  is_active={r[0]}  count={r[1]}")

    active = await conn.fetchval("SELECT COUNT(*) FROM schemes WHERE is_active = TRUE")
    inactive = await conn.fetchval("SELECT COUNT(*) FROM schemes WHERE is_active = FALSE")
    print(f"Active (is_active=TRUE):  {active}")
    print(f"Inactive (is_active=FALSE): {inactive}")

    # Check if status column exists
    has_status = await conn.fetchval(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='schemes' AND column_name='status'"
    )
    print(f"Has 'status' column: {bool(has_status)}")

    if has_status:
        rows2 = await conn.fetch(
            "SELECT status, COUNT(*) FROM schemes GROUP BY status ORDER BY status"
        )
        for r in rows2:
            print(f"  status={r[0]}  count={r[1]}")

    print()
    print("=" * 60)
    print("STEP 2 — SAMPLE ROWS")
    print("=" * 60)
    rows3 = await conn.fetch(
        "SELECT id, scheme_code, is_active, created_at FROM schemes "
        "ORDER BY created_at DESC LIMIT 10"
    )
    for r in rows3:
        print(f"  id={str(r[0])[:8]}...  code={r[1][:30]}  is_active={r[2]}  created={r[3]}")

    print()
    print("=" * 60)
    print("STEP 3 — COLUMNS IN schemes TABLE")
    print("=" * 60)
    cols = await conn.fetch(
        "SELECT column_name, data_type, column_default, is_nullable "
        "FROM information_schema.columns "
        "WHERE table_name='schemes' ORDER BY ordinal_position"
    )
    for c in cols:
        print(f"  {c[0]:30s}  {c[1]:20s}  default={c[2]}  nullable={c[3]}")

    await conn.close()


asyncio.run(run())
