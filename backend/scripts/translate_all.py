"""
Sahayak AI — Real Translation Pipeline
=========================================
Generates actual translated content via NLLB-200-distilled-600M.
- Deletes all fake (English-identical) translations
- Translates every active scheme into all 11 languages
- Stores results as published translations in the DB
- Resumes from where it left off (skip already translated)

Usage:
  python scripts/translate_all.py [--batch-size 8] [--limit 200] [--lang hi,ta]

Args:
  --batch-size N  : Number of texts per tokenizer batch (default: 4)
  --limit N       : Max schemes to process (default: ALL)
  --lang x,y,z   : Comma-separated language codes (default: all 11)
  --resume        : Skip schemes already having a valid (non-English) translation
  --clean         : Delete all existing fake translations first
"""

import asyncio
import argparse
import hashlib
import json
import logging
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, ".")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("translate_all")

# ── Language config ───────────────────────────────────────────────────────────
ALL_LANGS = ["hi", "ta", "te", "mr", "gu", "bn", "kn", "ml", "pa", "or", "as"]

NLLB_LANG = {
    "hi": "hin_Deva", "ta": "tam_Taml", "te": "tel_Telu",
    "mr": "mar_Deva", "gu": "guj_Gujr", "bn": "ben_Beng",
    "kn": "kan_Knda", "ml": "mal_Mlym", "pa": "pan_Guru",
    "or": "ory_Orya", "as": "asm_Beng",
}

# Fields to translate (text-bearing fields on Scheme model)
TRANSLATE_FIELDS = ["name", "short_description", "full_description", "benefits"]

# ── Checksum ──────────────────────────────────────────────────────────────────
def calc_checksum(d: dict) -> str:
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


# ── Deprecated engines removed ────────────────────────────────────────────────


# ── Database helpers ──────────────────────────────────────────────────────────
async def clean_fake_translations(db, langs: list[str]):
    """Delete translation records where translated name == English name."""
    from sqlalchemy import text
    for lang in langs:
        r = await db.execute(text(f"""
            DELETE FROM scheme_translations
            WHERE language_code = :lang
              AND translated_content->>'name' IN (
                  SELECT s.name FROM schemes s WHERE s.id = scheme_id
              )
        """), {"lang": lang})
        log.info(f"Deleted fake/English-identical translations for {lang}: {r.rowcount}")
    await db.commit()


async def get_already_translated_ids(db, lang: str) -> set:
    """Return scheme IDs that already have a valid (non-English) translation."""
    from sqlalchemy import text
    r = await db.execute(text("""
        SELECT st.scheme_id
        FROM scheme_translations st
        JOIN schemes s ON s.id = st.scheme_id
        WHERE st.language_code = :lang
          AND st.translated_content->>'name' IS DISTINCT FROM s.name
          AND (st.translated_content->>'name') != ''
    """), {"lang": lang})
    return {row[0] for row in r.fetchall()}

UNICODE_RANGES = {
    'hi': (0x0900, 0x097F),
    'mr': (0x0900, 0x097F),
    'ta': (0x0B80, 0x0BFF),
    'te': (0x0C00, 0x0C7F),
    'gu': (0x0A80, 0x0AFF),
    'bn': (0x0980, 0x09FF),
    'as': (0x0980, 0x09FF),
    'kn': (0x0C80, 0x0CFF),
    'ml': (0x0D00, 0x0D7F),
    'pa': (0x0A00, 0x0A7F),
    'or': (0x0B00, 0x0B7F),
}

def check_script(text, lang_code):
    if not text or not text.strip():
        return False
    if lang_code not in UNICODE_RANGES:
        return True
    
    start, end = UNICODE_RANGES[lang_code]
    for char in text:
        if start <= ord(char) <= end:
            return True
    return False

async def upsert_translation(db, scheme_id, lang: str, translated: dict, checksum: str, provider: str = "indictrans2"):
    """Insert or update a single translation record using ORM."""
    
    # DATABASE VALIDATION: Step 6
    if not translated or not translated.get("name"):
        log.warning(f"Rejecting empty translation for {scheme_id} in {lang}")
        return
        
    if not check_script(translated.get("name", ""), lang):
        log.warning(f"Rejecting corrupted unicode script for {scheme_id} in {lang}")
        return
        
    from sqlalchemy import select
    from app.models.translation import SchemeTranslation
    from app.models.enums import TranslationStatusEnum
    import uuid as _uuid

    scheme_id_val = _uuid.UUID(str(scheme_id))

    stmt = select(SchemeTranslation).where(
        SchemeTranslation.scheme_id == scheme_id_val,
        SchemeTranslation.language_code == lang,
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        existing.translated_content = translated
        existing.checksum = checksum
        existing.version = (existing.version or 0) + 1
        existing.status = TranslationStatusEnum.PUBLISHED
        existing.is_published = True
        existing.provider = provider
    else:
        new_rec = SchemeTranslation(
            scheme_id=scheme_id_val,
            language_code=lang,
            translated_content=translated,
            version=1,
            checksum=checksum,
            provider=provider,
            status=TranslationStatusEnum.PUBLISHED,
            is_published=True,
            manual_override=False,
        )
        db.add(new_rec)


# ── Main pipeline ─────────────────────────────────────────────────────────────
async def run(args):
    from app.database.database import AsyncSessionLocal
    from app.models.scheme import Scheme
    from sqlalchemy import select
    from sqlalchemy import text
    from app.services.translation.indictrans2_provider import IndicTrans2Provider

    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    log.info(f"Target languages: {langs}")
    log.info(f"Scheme limit: {args.limit or 'ALL'}")
    log.info(f"Clean fake: {args.clean}, Resume: {args.resume}")

    # Step A: Load schemes
    async with AsyncSessionLocal() as db:
        stmt = (
            select(Scheme)
            .where(Scheme.is_active == True)
            .order_by(Scheme.created_at)
        )
        if args.limit:
            stmt = stmt.limit(args.limit)
        result = await db.execute(stmt)
        schemes = list(result.scalars().all())
        log.info(f"Loaded {len(schemes)} active schemes")

        # Step B: Optionally clean fakes
        if args.clean:
            await clean_fake_translations(db, langs)

    # Step C: Load IndicTrans2 model
    log.info("Initializing IndicTrans2 Provider...")
    provider = IndicTrans2Provider()

    # Step D: Translate
    stats = {l: {"created": 0, "updated": 0, "failed": 0, "skipped": 0} for l in langs}
    total_done = 0
    grand_total = len(schemes) * len(langs)
    start_time = time.time()
    
    batch_size = args.batch_size

    for scheme in schemes:
        # Extract English text fields
        source = {
            "name": getattr(scheme, "name", "") or "",
            "short_description": getattr(scheme, "short_description", "") or "",
            "full_description": getattr(scheme, "full_description", "") or "",
            "benefits": getattr(scheme, "benefits", "") or "",
            "eligibility": "",
            "application_process": "",
            "required_documents": "",
            "faq": ""
        }
        
        # If the scheme has a JSON column like 'details' where these exist, extract them:
        if hasattr(scheme, "details") and isinstance(scheme.details, dict):
            source["eligibility"] = scheme.details.get("eligibility", "")
            source["application_process"] = scheme.details.get("application_process", "")
            source["required_documents"] = scheme.details.get("required_documents", "")
            source["faq"] = scheme.details.get("faq", "")
        checksum = calc_checksum(source)

        async with AsyncSessionLocal() as db:
            for lang in langs:
                try:
                    # Resume: skip if already validly translated
                    if args.resume:
                        already = await get_already_translated_ids(db, lang)
                        if scheme.id in already:
                            stats[lang]["skipped"] += 1
                            total_done += 1
                            continue

                    # Translate using provider's batch processing for JSON
                    translated = await provider.translate_json(source, "en", lang)

                    # Upsert
                    await upsert_translation(db, scheme.id, lang, translated, checksum)
                    await db.commit()

                    stats[lang]["created"] += 1
                    total_done += 1

                    # Progress log every 10 records to show Admin metrics
                    if total_done % 10 == 0 or total_done == grand_total:
                        elapsed = time.time() - start_time
                        rate = total_done / elapsed if elapsed > 0 else 0
                        eta = (grand_total - total_done) / rate if rate > 0 else 0
                        
                        mem_info = ""
                        import torch
                        if torch.cuda.is_available():
                            mem_alloc = torch.cuda.memory_allocated() / (1024**2)
                            mem_res = torch.cuda.memory_reserved() / (1024**2)
                            mem_info = f" | VRAM: {mem_alloc:.0f}MB / {mem_res:.0f}MB"

                        log.info(
                            f"Progress: {total_done}/{grand_total} "
                            f"({total_done/grand_total*100:.1f}%) "
                            f"| {rate*60:.1f} rec/min | ETA {eta/60:.1f}m{mem_info}"
                        )
                        log.info(
                            f"  Last: [{lang}] {scheme.name[:40]} → {translated.get('name','')[:40]}"
                        )

                except Exception as e:
                    log.error(f"FAILED: scheme={scheme.scheme_code} lang={lang}: {e}")
                    stats[lang]["failed"] += 1
                    total_done += 1
                    try:
                        await db.rollback()
                    except Exception:
                        pass

    # Step E: Final report
    elapsed = time.time() - start_time
    log.info("\n" + "=" * 60)
    log.info("TRANSLATION PIPELINE COMPLETE (IndicTrans2)")
    log.info("=" * 60)
    log.info(f"Total time: {elapsed/60:.1f} minutes")
    log.info(f"Total processed: {total_done}")
    for lang, s in stats.items():
        log.info(
            f"  {lang}: created={s['created']} updated={s['updated']} "
            f"skipped={s['skipped']} failed={s['failed']}"
        )

    # Step F: DB summary
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT language_code, COUNT(*) as cnt
            FROM scheme_translations
            WHERE is_published = TRUE
            GROUP BY language_code ORDER BY language_code
        """))
        log.info("\nPublished translations in DB:")
        for row in r:
            log.info(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=8, help="IndicTrans2 batch size")
    parser.add_argument("--limit",      type=int, default=0,  help="Max schemes (0=all)")
    parser.add_argument("--lang",       type=str, default=",".join(ALL_LANGS), help="Languages")
    parser.add_argument("--resume",     action="store_true", help="Skip already translated")
    parser.add_argument("--clean",      action="store_true", help="Delete fake translations first")
    args = parser.parse_args()
    asyncio.run(run(args))
