"""
Real Translation Pipeline — Sahayak AI
========================================
Uses the actual NLLB-200-distilled-600M model to translate schemes.
- Deletes all existing fake (English→English) translations
- Re-translates using real NLLB model
- Marks translations as PUBLISHED

Run:
  python scripts/run_real_translations.py [--limit N] [--lang hi,ta,te]

By default translates 100 schemes to ALL supported languages.
"""

import asyncio
import argparse
import sys
import logging
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, ".")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("real_translations")

SUPPORTED_LANGS = ["hi", "ta", "te", "mr", "gu", "bn", "kn", "ml", "pa", "or", "as"]

async def main(limit: int, langs: list[str], skip_delete: bool = False):
    from app.database.database import AsyncSessionLocal
    from sqlalchemy import text, select, delete
    from app.models.scheme import Scheme
    from app.models.translation import SchemeTranslation
    from app.models.enums import TranslationStatusEnum

    logger.info(f"Starting REAL translation pipeline")
    logger.info(f"Limit: {limit} schemes, Languages: {langs}")

    # Load NLLB model
    logger.info("Loading NLLB-200-distilled-600M model (this may take a few seconds)...")
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        model_name = "facebook/nllb-200-distilled-600M"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        device = "cpu"
        model = model.to(device)
        logger.info(f"Model loaded on {device}")
    except Exception as e:
        logger.error(f"Failed to load NLLB model: {e}")
        sys.exit(1)

    LANG_MAP = {
        "hi": "hin_Deva", "ta": "tam_Taml", "te": "tel_Telu",
        "mr": "mar_Deva", "gu": "guj_Gujr", "bn": "ben_Beng",
        "kn": "kan_Knda", "ml": "mal_Mlym", "pa": "pan_Guru",
        "or": "ory_Orya", "as": "asm_Beng",
    }

    def translate_text(text: str, tgt_lang_token: str) -> str:
        if not text or not text.strip():
            return text
        tokenizer.src_lang = "eng_Latn"
        inputs = tokenizer(
            text, return_tensors="pt", padding=True,
            truncation=True, max_length=512
        )
        forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang_token]
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=4,
            )
        return tokenizer.batch_decode(generated, skip_special_tokens=True)[0]

    async with AsyncSessionLocal() as db:
        if not skip_delete:
            # Delete fake translations for specified languages
            logger.info(f"Deleting existing fake translations for langs: {langs}")
            for lang in langs:
                result = await db.execute(text(
                    f"DELETE FROM scheme_translations WHERE language_code = '{lang}'"
                ))
            await db.commit()
            logger.info("Deleted existing translations")

        # Load schemes to translate
        result = await db.execute(
            select(Scheme)
            .where(Scheme.is_active == True)
            .order_by(Scheme.created_at)
            .limit(limit)
        )
        schemes = list(result.scalars().all())
        logger.info(f"Loaded {len(schemes)} schemes to translate")

        total = len(schemes) * len(langs)
        done = 0

        for scheme in schemes:
            fields = {
                "name": scheme.name or "",
                "short_description": scheme.short_description or "",
                "full_description": scheme.full_description or "",
                "benefits": scheme.benefits or "",
            }

            for lang in langs:
                tgt_lang_token = LANG_MAP.get(lang)
                if not tgt_lang_token:
                    continue

                translated = {}
                for field, value in fields.items():
                    if value.strip():
                        try:
                            translated[field] = translate_text(value, tgt_lang_token)
                        except Exception as e:
                            logger.warning(f"Translation failed for {field}: {e}")
                            translated[field] = value  # fallback to English
                    else:
                        translated[field] = ""

                # Save to DB
                import hashlib, json
                checksum = hashlib.sha256(
                    json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest()

                new_trans = SchemeTranslation(
                    scheme_id=scheme.id,
                    language_code=lang,
                    translated_content=translated,
                    version=1,
                    checksum=checksum,
                    provider="nllb-200-distilled-600M",
                    status=TranslationStatusEnum.PUBLISHED,
                    is_published=True,
                )
                db.add(new_trans)

                done += 1
                if done % 10 == 0 or done == total:
                    await db.commit()
                    logger.info(f"Progress: {done}/{total} ({done/total*100:.1f}%)")
                    logger.info(f"  Last: scheme={scheme.name[:40]} lang={lang} → {translated.get('name', '')[:50]}")

        await db.commit()
        logger.info(f"✅ Translation complete: {done} records written")

        # Verify
        r = await db.execute(text("""
            SELECT language_code, COUNT(*) as cnt
            FROM scheme_translations
            WHERE is_published = TRUE
            GROUP BY language_code ORDER BY language_code
        """))
        logger.info("Published translations:")
        for row in r:
            logger.info(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100, help="Number of schemes to translate")
    parser.add_argument("--lang", type=str, default=",".join(SUPPORTED_LANGS), help="Comma-separated language codes")
    parser.add_argument("--skip-delete", action="store_true", help="Skip deleting existing translations")
    args = parser.parse_args()

    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    asyncio.run(main(limit=args.limit, langs=langs, skip_delete=args.skip_delete))
