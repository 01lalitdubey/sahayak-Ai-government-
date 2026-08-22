"""Check which model columns are missing from the actual DB table."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import asyncpg

EXPECTED_COLUMNS = [
    'id', 'name', 'benefits', 'category', 'state', 'official_url',
    'is_active', 'created_at', 'updated_at', 'scheme_code', 'short_description',
    'full_description', 'scheme_type', 'ministry', 'department', 'district',
    'application_mode', 'application_start_date', 'application_end_date',
    'official_pdf_url', 'contact_email', 'contact_phone', 'is_featured',
    'view_count', 'created_by', 'updated_by',
    # These are the ones added in phase 4 that may be missing:
    'required_documents', 'application_process',
]

async def run():
    conn = await asyncpg.connect(
        'postgresql://sahayak:sahayak_password@localhost:5432/sahayak_db'
    )
    
    # Get actual columns
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='schemes' ORDER BY ordinal_position"
    )
    actual_cols = {r[0] for r in rows}
    print("=== ACTUAL COLUMNS IN DB ===")
    for c in sorted(actual_cols):
        print(f"  {c}")
    
    print()
    print("=== MISSING COLUMNS (in model but not in DB) ===")
    for col in EXPECTED_COLUMNS:
        if col not in actual_cols:
            print(f"  MISSING: {col}")
    
    print()
    print("=== EXTRA COLUMNS (in DB but not expected) ===")
    expected_set = set(EXPECTED_COLUMNS)
    for col in sorted(actual_cols):
        if col not in expected_set:
            print(f"  EXTRA: {col}")
    
    await conn.close()

asyncio.run(run())
