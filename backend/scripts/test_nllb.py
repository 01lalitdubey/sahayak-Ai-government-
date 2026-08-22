"""
Verify NLLB model produces real translations
"""
import sys
sys.path.insert(0, '.')

print("Loading NLLB-200-distilled-600M...")
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

print("Model loaded! Testing translation...")

test_texts = [
    "PM-KISAN scheme provides financial support to farmers.",
    "Scholarship for meritorious students from SC/ST category.",
    "Housing assistance for urban poor families.",
]

target_langs = {
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
}

for tgt_code, tgt_lang in target_langs.items():
    print(f"\n=== Translating to {tgt_code} ({tgt_lang}) ===")
    tokenizer.src_lang = "eng_Latn"
    
    for text in test_texts[:2]:  # Just test 2 texts
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
        
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=4,
            )
        translated = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        print(f"  EN: {text[:60]}")
        print(f"  {tgt_code}: {translated[:80]}")

print("\nDone!")
