#!/usr/bin/env python3
"""
paraphraser.py — Rewrite news titles into natural tweets via NVIDIA NIM (free).

Rules baked into prompt:
- Bahasa Indonesia santai tapi cerdas, kritis, TANPA template opener
- Variasi struktur kalimat (kadang pernyataan, kadang pertanyaan retoris, kadang opini)
- Max 240 chars, no hashtag spam, no emoji
- Kalau berita English, tetap tulis dalam bahasa Indonesia
- Fallback: kalau LLM gagal, pakai transformasi lokal sederhana
"""

import json
import urllib.request

NVIDIA_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.1-8b-instruct"

def _get_key():
    """Read NVIDIA key from Hermes config.yaml."""
    import re
    cfg = open(r"C:\Users\EMIS-07\AppData\Local\hermes\config.yaml", encoding="utf-8").read()
    m = re.search(r"nvidia:\s*\n\s*api_key:\s*(\S+)", cfg)
    return m.group(1) if m else None

SYSTEM_PROMPT = """Kamu menulis tweet untuk akun berita Indonesia yang kritis dan cerdas.
Aturan WAJIB:
- Tulis ulang berita jadi 1 tweet bahasa Indonesia, max 230 karakter
- GUNAKAN struktur kalimat yang BERBEDA dari judul asli (jangan copy-paste)
- Boleh kasih take/opini singkat yang tajam, atau pertanyaan retoris
- JANGAN mulai dengan frasa template seperti 'Menarik', 'Fakta baru', 'Catat ini'
- JANGAN pakai emoji, hashtag lebih dari 0-1, atau kata 'breaking'
- Gaya: percaya diri, lugas, sedikit kritis. Seperti analyst muda, bukan robot
- Output HANYA teks tweet, tanpa penjelasan apapun"""

def llm_paraphrase(title, summary="", source=""):
    """Paraphrase via NVIDIA. Returns str or None on failure."""
    key = _get_key()
    if not key:
        return None

    user_msg = f"Judul: {title}\n"
    if summary:
        user_msg += f"Ringkasan: {summary[:300]}\n"
    user_msg += "\nTulis tweet-nya."

    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 150,
        "temperature": 0.9,
    }).encode()

    req = urllib.request.Request(NVIDIA_BASE, data=payload, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
        text = data["choices"][0]["message"]["content"].strip()
        # bersihkan quotes pembungkus kadang ditambahkan model
        text = text.strip('"').strip()
        if len(text) < 20 or len(text) > 280:
            return None
        return text
    except Exception as e:
        print(f"[paraphraser] FAILED: {e}")
        return None

if __name__ == "__main__":
    out = llm_paraphrase(
        "Stability AI raises $76 million in fresh funding",
        "The company's new fundraising total now stands at $232 million.",
        "techcrunch"
    )
    print("RESULT:", out)
