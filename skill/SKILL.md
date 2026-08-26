# media-x-content-poster

Use when Boss wants to build an autonomous X media-posting system that:

- Pulls news/content from AI, affiliate, and Indonesian politics sources
- Transforms into varied content types (single tweet, thread, quote, retweet commentary)
- Posts ~1 post/hour to @penepian via CDP browser automation (no X API)
- Persists login session via dedicated Chrome profile
- Is fully reusable as a skill, idempotent, and pushed to GitHub

This skill covers the full pipeline: source fetching, content pipeline, scheduling queue, post executor, and session health monitoring.

## Session persistence (FIRST PRIORITY)

X sessions on Windows expire or clear themselves. This skill handles that explicitly:

- Dedicated Chrome profile at `C:/Users/EMIS-07/media-x-posting-profile` stores cookies + auth state
- Chrome launched with `--user-data-dir` pointing to this profile + `--remote-debugging-port=9222`
- Session health check runs before every post cycle: verify page is at X home, logged-in, article count >0
- If session is dead → STOP and report to Boss. Do NOT loop login attempts (X rate-limits login; Boss must manually re-login in the profile window)
- CDP port 9222 must be alive; if Chrome died, relaunch the profile (NOT any other Chrome instance)

**Never** touch Boss's personal Chrome. Only the dedicated profile.

## Pre-flight checklist (skill caller must ensure)

Before running any content-poster step, verify:

1. `C:/Users/EMIS-07/media-x-posting-profile` directory exists (we create it; do not delete)
2. Chrome launched with that profile on CDP port 9222 is running. Check: `curl http://127.0.0.1:9222/json/version` → 200 + "Profile Path" contains `media-x-posting-profile`
3. X session is alive: navigate to `https://x.com/home` and confirm article count > 0 (not login/captcha screen)
4. Hermes venv playwright installed (done once: `pip install playwright && playwright install chromium` in Hermes venv)

If any of these fail, the skill script should STOP and report — not retry blindly.

## LOGIN CACHE (SAVED 2026-08-26) — JANGAN HILANG

- **Akun X aktif**: @txtguru (display: txtdariguru) — BUKAN @penepian
- **Chrome profile**: `C:/Users/EMIS-07/media-x-posting-profile` (session persist di sini)
- **CDP port**: 9222 (`http://127.0.0.1:9222`)
- **Login status**: VERIFIED logged in (timeline + Post button terdeteksi)

### CARA RELAUNCH (kalau Chrome mati/reboot) — WAJIB ikuti urutan ini:

1. **JANGAN launch Chrome langsung dari Hermes** — Hermes jalan sebagai SYSTEM (Session 0), window TIDAK PERNAH muncul di desktop user. SetForegroundWindow/ShowWindow dari SYSTEM = gagal total.
2. **Cara benar**: scheduled task di sesi user:
   ```
   schtasks /Run /TN "MediaXChromeLaunch"
   ```
   Task ini menjalankan `launch_chrome_user.bat` dengan `/RU EMIS-07 /IT`.
3. **MODE SAAT INI: HEADLESS** (`--headless=new`, update 2026-08-26). Chrome jalan tanpa window sama sekali — zero visual disturbance. Session login TETAP persist di headless (terverifikasi). Kalau perlu login manual (session expired), edit .bat buang flag `--headless=new` dulu, jalankan task, Boss login, lalu balikin headless.
4. Kalau task hilang (reinstall), recreate:
   ```
   schtasks /Create /TN "MediaXChromeLaunch" /TR "C:\Users\EMIS-07\AppData\Local\hermes\skills\media-x-content-poster\launch_chrome_user.bat" /SC ONCE /ST 23:59 /RU "EMIS-07" /IT /F
   ```
5. Setelah relaunch, jalankan `session-check.py` untuk verifikasi login masih persist.

### Session expiry handling
- Session X bisa expire sewaktu-waktu. Kalau `session-check.py` bilang expired → STOP, laporkan ke Boss, minta login manual di Chrome profile itu. JANGAN loop login otomatis.

## Repository / GitHub

After building, push to Boss's GitHub (Jerukmer) under repo `media-x-posting`. Use `gh api` content upload if `git push` hangs from this Windows environment.

## Content pipeline snapshot

Sources (AI, affiliate, politics Indo) → fetch → filter/dedup → pick best → transform to content type → (LLM optional for paraphrase/tone) → queue → post executor → state update.

Content types: single tweet, thread (3-5 tweets), quote, retweet commentary. Tone varies (critical, analytical, straight, provocative-but-intelligent) — not locked to Gen Z pattern.

Rate: 1 post/hour, randomized within window (default 06:00–22:00 WIB). Outside window: queue sleeps.

Post executor (CDP): health check → compose text → submit → verify toast/redirect → log → update state. On failure: log + skip, don't freeze.

## Files in this skill

- `SKILL.md` — this file
- `profile-launch.py` — launch Chrome with dedicated profile + CDP port, verify
- `session-check.py` — verify X session alive via CDP
- `post-executor.py` — compose + post 1 tweet via CDP (single post only; thread expansion separate)
- `state.py` — dedupe + track posted items (SQLite or JSON)
- `pipeline.py` — source fetch + content transformation (stub; fill in sources later)
- `runner.py` — orchestrator: runs pipeline → queue → post executor on schedule

## Known limitations

- X session may expire; manual re-login required when dead (no auto-login loop)
- CDP via Playwright on Windows may timeout; fallback to CDP HTTP endpoints (cdp_http.py pattern)
- Rate limits are X-side, not code bugs; respect pauses
- This is a foundational skill; sources and content transformation fill in later

---

## How to invoke

### 1. Launch profile (one-time or after crash)

```bash
cd C:/Users/EMIS-07/AppData/Local/hermes/skills/media-x-content-poster
C:/Users/EMIS-07/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe profile-launch.py
```

### 2. Verify session

```bash
cd same dir
C:/Users/EMIS-07/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe session-check.py
```

### 3. Post (manual test)

Edit `test-post.txt` with your tweet text, then run `post-executor.py`.

### 4. Full pipeline (future)

Once sources and pipeline are filled, `runner.py` runs every hour via cron.

---

## References

- `references/windows-chrome-cdp.md` — CDP setup notes for this machine
- `references/x-session-expiry.md` — X session behavior notes
