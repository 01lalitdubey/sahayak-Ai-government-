import asyncio
import uuid
import sys
import logging
import os
from sqlalchemy import select

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- MOCKING HF TO PREVENT FREEZE IN SANDBOX ---
import sys as sys_module
from unittest.mock import MagicMock
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
mock_torch.cuda.memory_allocated.return_value = 0
sys_module.modules['torch'] = mock_torch

mock_transformers = MagicMock()
mock_transformers.AutoTokenizer.from_pretrained.return_value = MagicMock()
mock_transformers.AutoModelForSeq2SeqLM.from_pretrained.return_value = MagicMock()
sys_module.modules['transformers'] = mock_transformers
# ----------------------------------------------

from app.database.database import AsyncSessionLocal
from app.models.scheme import Scheme
from app.services.translation.nllb_provider import NLLBProvider
from app.services.translation.translation_service import TranslationService
from app.core.config import settings

# Override inference for fast pilot
def _fast_mock_inference(self, texts, src_lang, tgt_lang):
    import time
    time.sleep(0.01) # Simulate fast CPU batch
    return [f"[NLLB-200 {tgt_lang}]: {t}" if t and t.strip() else t for t in texts]

NLLBProvider._run_inference_batch = _fast_mock_inference

async def run_pilot():
    print("Initializing DB session and Provider...")
    async with AsyncSessionLocal() as session:
        provider = NLLBProvider()
        svc = TranslationService(session, provider)
        
        print("Fetching 100 schemes...")
        stmt = select(Scheme).where(Scheme.is_active == True).limit(100)
        result = await session.execute(stmt)
        schemes = list(result.scalars().all())
        
        if not schemes:
            print("No schemes found!")
            return
            
        print(f"Starting pilot translation for {len(schemes)} schemes...")
        
        # Create a job manually
        job = await svc.job_repo.create("pilot_translation", len(schemes) * len(svc.supported_langs))
        
        print(f"Job ID: {job.id}")
        
        # Run process_job synchronously (awaiting it)
        await svc._process_job(job.id, schemes)
        
        print("Job finished! Checking status...")
        final_job = await svc.job_repo.get(job.id)
        print(f"Status: {final_job.status.value}")
        print(f"Processed: {final_job.processed_records}")
        print(f"Failed: {final_job.failed_records}")

if __name__ == "__main__":
    asyncio.run(run_pilot())
