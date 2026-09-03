# Sahayak AI — RAG / Voice Assistant

Multilingual retrieval-augmented assistant for Indian government schemes.

## Pipeline

```
Voice / Text
  → Whisper large-v3 (Groq)            transcription + spoken-language hint
  → Language Resolution                selected code wins; else ASR lang; else text-detect
  → openai/gpt-oss-20b (Groq)          user question → English (for retrieval only)
  → all-MiniLM-L6-v2                   384-dim query embedding
  → Vector store (ChromaDB / local)    top-k scheme chunks, cosine similarity
  → Deterministic eligibility rules    per retrieved scheme, for signed-in users
  → openai/gpt-oss-120b (Groq)         grounded answer generated DIRECTLY in the
                                       resolved language (context-only)
  → Sources                            scheme name, code, links, eligibility status
  → TTS router (gTTS / MMS-TTS)         audio in the resolved language — all 13
```

> Note: `allam-2-7b` (from the original spec) is an Arabic-only model and
> produces degenerate output for Indic languages, so translation uses
> `openai/gpt-oss-20b` and the answer is written straight into the target
> language by `gpt-oss-120b` — one fewer LLM hop, no lossy round-trip.
> Both are overridable via `GROQ_TRANSLATION_MODEL` / `GROQ_ANSWER_MODEL`.

Everything is orchestrated by `app/services/rag/pipeline.py::RagPipeline`.

## Endpoints (`/api/v1/rag`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/languages` | none | 13 languages + `auto`, with per-language TTS availability |
| `GET` | `/health` | none | pipeline config, models, index size |
| `POST` | `/query` | optional | `{query, language}` → localized answer + sources |
| `POST` | `/voice` | optional | multipart `audio` + `language` → answer + sources + `audio_url` |
| `GET` | `/audio/{name}` | none | fetch a generated gTTS mp3 |
| `POST` | `/ingest` | **admin** | (re)build the scheme vector index |

`language` is one of the 13 codes or `"auto"`. When a **concrete code** is sent it
**always** controls the answer language and the TTS voice, regardless of what
language the question is in. `"auto"` resolves to exactly one concrete code
(never `"auto"`), using the ASR-detected language for voice, or script + keyword
detection for text.

Signed-in callers (Bearer token) additionally get deterministic eligibility
results for each retrieved scheme folded into the answer and the `sources[]`.
Anonymous callers get the answer without personalised eligibility.

## The 13 languages

`en, hi, ur, bn, as, ta, te, mr, gu, kn, ml, pa, or` — registry in
`app/services/rag/languages.py`.

* **Hindi ≠ Urdu** — different scripts (Devanagari vs Perso-Arabic); Perso-Arabic
  text always resolves to `ur`, never `hi`.
* **Bengali ≠ Assamese** — same script; disambiguated by the Assamese-only
  letters `ৰ` / `ৱ`, an Assamese word list, then a `langdetect` fallback.
* **TTS**: every one of the 13 languages has a voice. A provider abstraction
  (`app/services/rag/tts_providers.py`) routes per language:
  * **gTTS** — 11 languages (all except Odia/Assamese). Fast, no model.
  * **MMS** — `facebook/mms-tts-<iso3>` VITS, **offline**, covers **all 13**
    including Odia (`ory`), Assamese (`asm`) and Urdu (`urd-script_arabic`).
    It synthesises the actual target-language text — it never substitutes
    another language. ~145 MB/model, downloaded on first use, LRU-capped.
  * Order is set by `RAG_TTS_PROVIDER` (`auto` | `gtts` | `mms`); MMS is always
    the final fallback, so a transient gTTS failure can't silence a language.
  Generated clips are `<uuid>.mp3` (gTTS) or `<uuid>.wav` (MMS); the
  `/api/v1/rag/audio/{name}` route serves both with the right content-type.
  `tts_available` is now `true` for all 13 (it reflects backend capability;
  `audio_url == null` on a given response means synthesis failed that time).

`backend/tests/test_rag_languages.py` (51 cases) verifies all 13 detect to
themselves, hi≠ur, bn≠as, that a selected language always wins, and that
Whisper's language labels (`"tamil"`, `"ta"`, `"en-US"`, …) all resolve via the
ASR branch.

## Verification status (last run)

Index: **4,569 active schemes** ingested into the `local` NumPy store.

| Check | Result |
|---|---|
| Selected-language mode, all 13 languages (English query → answer in target, grounded, sources, TTS) | **13/13 PASS** |
| Auto-detect, native-script queries (hi, ur, bn, as, ta, or) → correct concrete language | **6/6 PASS** |
| Voice: gTTS-synthesised question → `/rag/voice` → Whisper → resolution → answer → TTS (hi, ta, bn, en) | **4/4 PASS** (`language_source = asr`) |
| Authenticated query → deterministic eligibility folded into `sources[].eligibility_status` | **PASS** |
| `chat_history` row written with correct language enum | **PASS** |

Notes:
* The DB currently holds **0 `eligibility_rules`**, so every scheme evaluates to
  `no_rules` → `eligibility_status = "No eligibility restrictions recorded"`.
  The integration is wired and exercised; it will produce eligible / not-eligible
  verdicts as soon as rules exist.

### 13-language voice / TTS (post TTS-router change)

| Check | Result |
|---|---|
| **TTS layer** — every language synthesises playable audio (direct, no Groq): file valid, `/audio/{name}` serves it, correct content-type | **13/13 PASS** — 11 mp3 via gTTS, **Odia + Assamese wav via MMS-TTS** |
| End-to-end voice (speech → Whisper → resolve → RAG → answer in target script → TTS → playable) | **12/13 verified** (en hi ur bn ta te as via voice; mr gu kn ml pa via voice; **or** via text path + components) |
| Marathi answer script (gpt-oss romanised it) | fixed by the **script guard** in `pipeline.py` — retries once in native script, then transliterates; `mr` now returns Devanagari |
| Odia Whisper hint | `whisper-large-v3` has no `or` hint → omitted; ASR auto-detects, `resolve_language` still forces Odia answer + Odia MMS voice |

Auto-detect **over voice** is limited by Whisper's language-ID on script-sibling
pairs (hi/mr, kn/te, ml/ta, pa/hi, bn/as) and on synthetic test audio — for
those, users should pick their language (the 13-way selector); the selected
language then controls answer + TTS deterministically.

## Configuration (`backend/.env`)

```env
GROQ_API_KEY=...                 # one key → Whisper + gpt-oss-20b + gpt-oss-120b
GROQ_WHISPER_MODEL=whisper-large-v3
GROQ_TRANSLATION_MODEL=openai/gpt-oss-20b
GROQ_ANSWER_MODEL=openai/gpt-oss-120b

RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_CHROMA_MODE=local            # local (numpy, default) | persistent | http
RAG_CHROMA_PATH=chroma_db
RAG_TOP_K=3
RAG_MAX_QUERY_CHARS=1000

RAG_ENABLE_ASR=true
RAG_ENABLE_TTS=true
RAG_AUDIO_DIR=app/static/rag_audio
```

`RAG_CHROMA_MODE`:
* **`local`** (default) — pure-NumPy store persisted to `RAG_CHROMA_PATH`.
  Zero native dependencies; works everywhere including Windows without build tools.
* **`persistent`** — `chromadb.PersistentClient`. Requires the full `chromadb`
  package (uncomment it in `requirements.txt`; Windows needs MSVC for
  `chroma-hnswlib`).
* **`http`** — `chromadb.HttpClient` against a Chroma server. Uncomment the
  `chroma` service in `docker-compose.yml`.

If `GROQ_API_KEY` is unset, every RAG endpoint returns `503` and the chat UI
shows a "not configured" banner.

## First-run

```bash
# 1. set GROQ_API_KEY in backend/.env
# 2. build the index from active schemes:
cd backend
python -m app.services.rag.ingest
#    (or: POST /api/v1/rag/ingest  as an admin)
# 3. frontend: NEXT_PUBLIC_ENABLE_CHAT=true, NEXT_PUBLIC_ENABLE_VOICE=true
```

Re-run ingestion whenever schemes or their eligibility rules change.

## Frontend

* `src/services/rag.service.ts` · `src/hooks/use-rag.ts`
* `src/app/[locale]/chat/ChatClient.tsx` — text + mic input, language selector
  (Auto + 13), streamed transcript, audio playback, collapsible sources.
* Urdu (`ur`) is now a first-class locale (`i18n/routing.ts`, `language-store.ts`,
  `lib/axios.ts`) with RTL handling in the chat view.
