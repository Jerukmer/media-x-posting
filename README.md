# media-x-posting

Autonomous X posting system for @txtguru. 1 post/hour, keyless RSS news sources (AI, affiliate/business, Indonesian politics), CDP browser automation (no X API).

## Architecture

```
sources.py       → fetch RSS feeds (keyless)
pipeline.py      → transform to tweet text (varied tones)
state.py         → SQLite dedupe + posted history
post_executor.py → post via Chrome CDP port 9222 (careful mode)
runner.py        → orchestrator, run 1x/hour
```

## Setup (EMIS-07 specific)

1. Chrome dedicated profile: `C:/Users/EMIS-07/media-x-posting-profile`, CDP port 9222.
2. Relaunch via scheduled task, HEADLESS mode (no window, session persists):
   ```
   schtasks /Run /TN "MediaXChromeLaunch"
   ```
3. Login @txtguru manually once — session persists in profile.
4. Verify: `python session-check.py` (copy from Hermes skill `media-x-content-poster`).
5. Install deps (Hermes venv has playwright):
   ```
   pip install playwright && playwright install chromium
   ```

## Run

```bash
python runner.py            # one cycle (fetch→post max 1 tweet)
python runner.py --dry-run  # TODO: preview without posting
python post_executor.py "test text"   # manual single post
```

## Schedule (Windows)

```bash
schtasks /Create /TN "MediaXPostingHourly" /TR "C:\...\venv\Scripts\python.exe C:\Users\EMIS-07\media-x-posting\runner.py" /SC HOURLY /RU SYSTEM /F
```
Runner itself respects active hours 06:00–22:00 WIB.

## Safety rules

- Pre-check session alive before every post; abort on expired (no login loops)
- Max 1 post/run; randomized tone; dedupe by link in SQLite
- Post failure = log + exit non-zero; caller decides retry policy
- Never touch Boss's personal Chrome

## Roadmap

- [ ] Thread content type (3–5 tweets)
- [ ] Quote tweets + retweet commentary
- [ ] Engagement-based scoring for picking best item
- [ ] LLM-assisted paraphrase (optional, via local 9Router)
- [ ] Dry-run mode
- [ ] Telegram report after each post
