import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model_name = "naklitechie/indictrans2-en-indic-dist-200M"
cache_dir = "models/indictrans2"

tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir, trust_remote_code=True, src_lang="eng_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=cache_dir, trust_remote_code=True).to("cuda")

texts = ["Hello, this is a test."]
tgt_lang_code = "hin_Deva"
tgt_lang_id = tokenizer.convert_tokens_to_ids(tgt_lang_code)
print(f"Target Lang ID for {tgt_lang_code}: {tgt_lang_id}")

inputs = tokenizer(texts, return_tensors="pt").to("cuda")
print(f"Input IDs: {inputs.input_ids}")

with torch.no_grad():
    generated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=tgt_lang_id,
        max_length=512,
        num_beams=4,
    )

decoded = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
print(f"Decoded: {decoded}")
