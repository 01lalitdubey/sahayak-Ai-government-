# Security

## Reporting a vulnerability

Please open a private security advisory on the repository, or email the
maintainer listed in `package.json` / `pyproject`. Do not file a public issue
for anything exploitable.

## Configuration that matters

- **`SECRET_KEY`** — signs every JWT. The backend refuses to start when
  `APP_ENV` is not `development` and the key is empty, a shipped placeholder,
  or shorter than 32 characters. Generate one with
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- **`.env` files are never committed.** They are covered by `.gitignore`; the
  templates are `*.env.example`. If a real credential ever lands in a commit,
  rotate it at the provider and scrub history before pushing.
- **`GROQ_API_KEY`** — powers the RAG assistant. `/rag/query` and `/rag/voice`
  require authentication and are rate-limited (`RAG_RATE_LIMIT`, default
  `30/minute` per user) because each call costs money.
- **CORS** — `APP_ENV=development` allows all origins for local convenience;
  every other environment uses the explicit `ALLOWED_ORIGINS` allowlist.

## Known hardening follow-ups (not yet implemented)

- **Refresh-token revocation.** Access and refresh tokens are stateless JWTs
  with no server-side store. A refresh token stays valid until it expires and
  `logout` is client-side only. Planned fix: a `jti` denylist in Redis for
  single-use refresh tokens and real logout.
- **Token storage in the browser.** The frontend keeps tokens in
  `localStorage`, which is readable by any XSS. Planned fix: `httpOnly`
  cookies plus CSRF protection.
- **Login brute-force.** No lockout or CAPTCHA on `/auth/login` yet.
