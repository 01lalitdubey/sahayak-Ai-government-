"""
Check which columns are in the ORM model but missing from the DB table.
"""
import asyncio
import asyncpg

# From the ORM model inspection, these are the expected columns:
EXPECTED_COLS = {
    "id", "name", "benefits", "category", "state", "official_url",
    "is_active", "created_at", "updated_at", "scheme_code",
    "short_description", "full_description", "scheme_type",
    "ministry", "department", "district", "application_mode",
    "application_start_date", "application_end_date",
    "official_pdf_url", "contact_email", "contact_phone",
    "is_featured", "view_count", "created_by", "updated_by",
    "required_documents", "application_process"
}


async def check_columns():
    conn = await asyncpg.connect(
        "postgresql://sahayak:sahayak_password@localhost:5432/sahayak_db"
    )
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'schemes'"
    )
    actual_cols = {r["column_name"] for r in rows}

    print("=== ACTUAL DB COLUMNS ===")
    for c in sorted(actual_cols):
        print(f"  {c}")

    missing = EXPECTED_COLS - actual_cols
    extra = actual_cols - EXPECTED_COLS

    print(f"\n=== MISSING (in ORM but NOT in DB): {len(missing)} ===")
    for c in sorted(missing):
        print(f"  MISSING: {c}")

    print(f"\n=== EXTRA (in DB but NOT in ORM): {len(extra)} ===")
    for c in sorted(extra):
        print(f"  EXTRA: {c}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_columns())
