#!/usr/bin/env python3
"""
commentary.py — Generate critical commentary tweets from screening findings.

Uses llm_client (NVIDIA + template fallback). Critical, educational tone.
"""

from llm_client import make_commentary

def generate(finding):
    """finding: dict with 'user', 'keys', 'snippet'. Returns commentary str (LLM or fallback)."""
    return make_commentary(finding)

if __name__ == "__main__":
    test = {"user": "@randomdev", "keys": [("openai-sk", "sk-…abcd")], "snippet": "free api key guys"}
    out = generate(test)
    print("COMMENTARY:", out)
