"""Measures the Arabic token tax on Claude with your own API key (free endpoint).

    export ANTHROPIC_API_KEY=...    pip install anthropic
    python count_claude.py --model claude-sonnet-5-5
Not run here, because this project was built without an API key.
"""
import argparse
import anthropic
from tax.measure import text

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="claude-sonnet-5-5")
a = ap.parse_args()
client = anthropic.Anthropic()
counts = {}
for code, name in (("eng", "English"), ("arb", "Arabic"), ("ckb", "Kurdish (Sorani)"), ("pes_1", "Persian")):
    counts[name] = client.messages.count_tokens(model=a.model, messages=[{"role": "user", "content": text(code)}]).input_tokens
for k, v in counts.items():
    print(f"{k:18s} {v:7,d} tokens   {v / counts['English']:.2f}× English")
