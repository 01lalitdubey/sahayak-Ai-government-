"""
Forensic DB audit script for Sahayak AI scheme investigation.
"""
import asyncio
import asyncpg


async def audit():
    conn = await asyncpg.connect(
        "postgresql://sahayak:sahayak_password@localhost:5432/sahayak_db"
    )

    # 1. Total count
    total = await conn.fetchval("SELECT COUNT(*) FROM schemes")
    print(f"\n=== TOTAL SCHEMES: {total} ===")

    # 2. is_active breakdown
    rows = await conn.fetch(
        "SELECT is_active, COUNT(*) as cnt FROM schemes GROUP BY is_active ORDER BY is_active"
    )
    print("\n--- is_active breakdown ---")
    for r in rows:
        print(f"  is_active={r['is_active']}: {r['cnt']}")

    # 3. Active count specifically
    active_count = await conn.fetchval("SELECT COUNT(*) FROM schemes WHERE is_active = true")
    print(f"\n--- Active (is_active=TRUE): {active_count} ---")

    # 4. NULL is_active (if any)
    null_count = await conn.fetchval("SELECT COUNT(*) FROM schemes WHERE is_active IS NULL")
    print(f"--- NULL is_active: {null_count} ---")

    # 5. Recent 5 schemes
    recent = await conn.fetch(
        "SELECT id, scheme_code, name, is_active, created_at FROM schemes ORDER BY created_at DESC LIMIT 5"
    )
    print("\n--- 5 Most Recent Schemes ---")
    for r in recent:
        code = r["scheme_code"]
        is_active = r["is_active"]
        created_at = r["created_at"]
        print(f"  code={code} | is_active={is_active} | created_at={created_at}")

    # 6. Check if there's a 'status' column
    has_status = await conn.fetchval(
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name='schemes' AND column_name='status'
        """
    )
    print(f"\n--- Has 'status' column: {has_status > 0} ---")

    # 7. Actual columns on the schemes table
    cols = await conn.fetch(
        """
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = 'schemes'
        ORDER BY ordinal_position
        """
    )
    print("\n--- Schemes table columns ---")
    for c in cols:
        print(f"  {c['column_name']:30s} {c['data_type']:20s} default={c['column_default']}")

    await conn.close()
    print("\n=== AUDIT COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(audit())
