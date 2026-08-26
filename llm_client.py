#!/usr/bin/env python3
"""
llm_client.py — Unified LLM client with fallback chain.

Try order:
1. NVIDIA NIM (if key configured & model alive)
2. Template fallback (always works, no network)

Usage:
    from llm_client import rewrite_news, make_commentary
"""

import json
import urllib.request
import re
import random

NVIDIA_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.1-8b-instruct"  # EOL-prone; update if needed

NEWS_SYSTEM = """Kamu menulis tweet untuk akun berita Indonesia yang kritis dan cerdas.
Aturan WAJIB:
- Tulis ulang berita jadi 1 tweet bahasa Indonesia, max 230 karakter
- GUNAKAN struktur kalimat yang BERBEDA dari judul asli
- Boleh kasih take/opini singkat yang tajam, atau pertanyaan retoris
- JANGAN mulai dengan frasa template seperti 'Menarik', 'Fakta baru', 'Catat ini'
- JANGAN pakai emoji, hashtag lebih dari 0-1
- Output HANYA teks tweet, tanpa penjelasan"""

COMMENTARY_SYSTEM = """Kamu analis keamanan AI yang kritis tapi santai, nulis di X bahasa Indonesia.
Tugas: KOMENTARI (bukan promosikan) kebiasaan orang membagikan API key gratis di X.
Sudut pandang: skeptis, edukatif, anti-scam. Ingatkan bahaya: key dicabut, akun banned,
data disedot, atau honeypot. Tulis cerdas, bukan alarmis. Max 220 karakter.
JANGAN sebut isi key. JANGAN hashtag spam. 1 tweet aja."""

NEWS_FALLBACKS = [
    "Ada kabar baru soal {topic}. Menarik lihat gimana ini bakal ngaruh ke ekosistem dalam beberapa bulan ke depan.",
    "{topic}. Pertanyaan nyata: ini solusi beneran atau sekadar hype yang kebentur realita nanti?",
    "{topic} — perkembangan yang layak diawasi, bukan cuma karena ramai, tapi karena pangkalnya.",
]

COMMENTARY_FALLBACKS = [
    "Orang bagi API key gratis di X — jangan langsung copas. Sering trap: dicabut mendadak, akun keban, atau data lo yang disedot. Free tier resmi selalu lebih aman.",
    "Lihat banyak bagi-bagi API key 'gratis' di sini. Realitanya? Key ilang dalam hari, atau malah honeypot buat ngerekam traffic lo. Pakai tier gratis official aja.",
    "Bagi API key di timeline = red flag. Bisa jadi promosi legit, tapi bisa juga jebakan phising. Kalau gratisan di X, cross-check dulu sebelum pakai.",
]

def _get_nvidia_key():
    try:
        cfg = open(r"C:\Users\EMIS-07\AppData\Local\hermes\config.yaml", encoding="utf-8").read()
        m = re.search(r"nvidia:\s*\n\s*api_key:\s*(\S+)", cfg)
        return m.group(1) if m else None
    except Exception:
        return None

def _nv_call(system, user, max_tokens=150):
    key = _get_nvidia_key()
    if not key:
        return None
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.85,
    }).encode()
    req = urllib.request.Request(NVIDIA_BASE, data=payload, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip().strip('"')
    except Exception:
        return None

def rewrite_news(title, summary="", source=""):
    """Rewrite news to tweet. LLM-first, fallback template."""
    out = _nv_call(NEWS_SYSTEM, f"Judul: {title}\nRingkasan: {summary[:300]}\nTulis tweet-nya.")
    if out and 20 <= len(out) <= 280:
        return out
    topic = title[:80]
    return random.choice(NEWS_FALLBACKS).format(topic=topic)

def make_commentary(finding):
    """Make critical commentary from screening finding. LLM-first, fallback template."""
    user = finding.get("user", "seseorang")
    key_types = ", ".join(sorted(set(k[0] for k in finding.get("keys", []))))
    out = _nv_call(COMMENTARY_SYSTEM, f"Di X, {user} bagi API key gratis (tipe: {key_types}). Komentar kritis lo?")
    if out and 20 <= len(out) <= 280:
        return out
    return random.choice(COMMENTARY_FALLBACKS)

if __name__ == "__main__":
    print("NEWS:", rewrite_news("Stability AI raises $76M", "Funding round closed."))
    print("COMMENT:", make_commentary({"user": "@x", "keys": [("openai-sk", "sk-..ab")]}))
