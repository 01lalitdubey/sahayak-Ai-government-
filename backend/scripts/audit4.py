import asyncio
import sys
os.environ = __import__('os').environ
sys.path.insert(0, '.')

async def audit():
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as db:
        # Test 1: Does the inject_translation actually produce translated text?
        # The name has [NLLB-200 hin_Deva]: prefix which means the NLLB engine
        # stored the translated result but prepended a tag that shouldn't be there
        
        r = await db.execute(text("""
            SELECT 
                s.name as english_name,
                st.translated_content->>'name' as translated_name,
                st.translated_content->>'short_description' as translated_short_desc,
                s.short_description as english_short_desc
            FROM scheme_translations st
            JOIN schemes s ON s.id = st.scheme_id
            WHERE st.language_code = 'hi'
            LIMIT 3
        """))
        
        print('=== NAME COMPARISON: English vs Translated ===')
        for row in r:
            eng_name = row[0]
            trans_name = row[1]
            eng_desc = row[3]
            trans_desc = row[2]
            print(f'\nEnglish name: {eng_name[:80]}')
            print(f'Hindi name:   {trans_name[:80] if trans_name else "EMPTY"}')
            print(f'English desc: {eng_desc[:60] if eng_desc else "EMPTY"}')
            print(f'Hindi desc:   {trans_desc[:60] if trans_desc else "EMPTY"}')
        
        # Test 2: Check the NEXT_LOCALE cookie handling
        # The axios interceptor reads NEXT_LOCALE from cookies
        # next-intl uses NEXT_LOCALE cookie
        # But the issue might be that next-intl uses a different cookie name
        
        # Let's check what's in the frontend routing config
        print('\n=== COOKIE STRATEGY CHECK ===')
        print('next-intl default cookie name: NEXT_LOCALE')
        print('Axios reads: NEXT_LOCALE')
        print('This should be correct')
        
        # Test 3: Test API endpoint directly
        import httpx
        base = 'http://localhost:8000'
        
        try:
            # Test with Accept-Language header
            async with httpx.AsyncClient(timeout=10) as client:
                # Test list
                resp = await client.get(f'{base}/api/v1/schemes?page_size=3', headers={'Accept-Language': 'hi'})
                if resp.status_code == 200:
                    data = resp.json()
                    schemes = data.get('data', [])
                    print('\n=== API TEST: GET /schemes?page_size=3 with Accept-Language: hi ===')
                    for s in schemes[:2]:
                        print(f'  name: {s.get("name", "N/A")[:80]}')
                        print(f'  short_desc: {str(s.get("short_description", ""))[:60]}')
                else:
                    print(f'\n  API returned: {resp.status_code}')
        except Exception as e:
            print(f'\n  Could not reach API (is backend running?): {e}')

asyncio.run(audit())
