import asyncio
import asyncpg
import json
import re

UNICODE_RANGES = {
    'hi': (0x0900, 0x097F), # Devanagari
    'mr': (0x0900, 0x097F), # Devanagari
    'ta': (0x0B80, 0x0BFF), # Tamil
    'te': (0x0C00, 0x0C7F), # Telugu
    'gu': (0x0A80, 0x0AFF), # Gujarati
    'bn': (0x0980, 0x09FF), # Bengali
    'as': (0x0980, 0x09FF), # Bengali (Assamese)
    'kn': (0x0C80, 0x0CFF), # Kannada
    'ml': (0x0D00, 0x0D7F), # Malayalam
    'pa': (0x0A00, 0x0A7F), # Gurmukhi
    'or': (0x0B00, 0x0B7F), # Odia
}

def check_script(text, lang_code):
    """Returns True if the text contains characters from the correct Unicode block."""
    if not text or not text.strip():
        return False
    if lang_code not in UNICODE_RANGES:
        return True # Skip checking if not mapped
    
    start, end = UNICODE_RANGES[lang_code]
    for char in text:
        if start <= ord(char) <= end:
            return True
    return False

async def main():
    c = await asyncpg.connect('postgresql://sahayak:sahayak_password@localhost/sahayak_db')
    
    report = {
        "total_schemes": await c.fetchval('SELECT COUNT(*) FROM schemes'),
        "total_translations": await c.fetchval('SELECT COUNT(*) FROM scheme_translations'),
        "by_language": {},
        "status_counts": {},
        "duplicates": await c.fetchval('SELECT COUNT(*) FROM (SELECT scheme_id, language_code, COUNT(*) FROM scheme_translations GROUP BY scheme_id, language_code HAVING COUNT(*) > 1) as dupes'),
        "corrupted": 0,
        "english_copied": 0,
        "wrong_script": 0,
        "empty_or_whitespace": 0,
        "total_sampled": 0
    }
    
    by_lang = await c.fetch('SELECT language_code, COUNT(*) FROM scheme_translations GROUP BY language_code')
    for row in by_lang:
        report["by_language"][row['language_code']] = row['count']
        
    by_status = await c.fetch('SELECT status, COUNT(*) FROM scheme_translations GROUP BY status')
    for row in by_status:
        report["status_counts"][row['status']] = row['count']
        
    # Sample 200 records
    samples = await c.fetch('''
        SELECT t.id, t.language_code, t.translated_content, s.name as original_name 
        FROM scheme_translations t 
        JOIN schemes s ON t.scheme_id = s.id 
        ORDER BY RANDOM() LIMIT 200
    ''')
    
    report["total_sampled"] = len(samples)
    
    for row in samples:
        lang = row['language_code']
        try:
            content = json.loads(row['translated_content'])
            trans_name = content.get('name', '')
            
            if not trans_name or not str(trans_name).strip():
                report["empty_or_whitespace"] += 1
                report["corrupted"] += 1
                continue
                
            if str(trans_name).strip().lower() == str(row['original_name']).strip().lower():
                report["english_copied"] += 1
                report["corrupted"] += 1
                continue
                
            if not check_script(str(trans_name), lang):
                report["wrong_script"] += 1
                report["corrupted"] += 1
                continue
                
        except Exception:
            report["corrupted"] += 1
            
    await c.close()
    
    with open('qa_db_results.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print("DB QA Complete. Results written to qa_db_results.json")

asyncio.run(main())
