"""All measurements. Every number in the README and the workbook comes from here."""
import json, pathlib, regex, unicodedata
from collections import Counter
from .tokenizers import load_all

ROOT = pathlib.Path(__file__).resolve().parents[1]
LANGS = {"eng": "English", "arb": "Arabic", "ckb": "Kurdish (Sorani)", "pes_1": "Persian", "urd": "Urdu", "heb": "Hebrew",
         "tur": "Turkish", "fra": "French", "spa": "Spanish", "deu": "German", "por_BR": "Portuguese", "ita": "Italian",
         "ind": "Indonesian", "swh": "Swahili", "vie": "Vietnamese", "rus": "Russian", "ell_monotonic": "Greek",
         "hin": "Hindi", "ben": "Bengali", "tha": "Thai", "amh": "Amharic", "cmn_hans": "Chinese", "jpn": "Japanese", "kor": "Korean"}
ARABIC = regex.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
WORD = regex.compile(r"\p{L}[\p{L}\p{M}]*")
EASTERN = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def text(code):
    raw = (ROOT / "data" / "udhr2" / f"{code}.txt").read_text(encoding="utf8")
    return unicodedata.normalize("NFC", " ".join(raw.split()))


def run():
    toks = load_all()
    texts = {c: text(c) for c in LANGS}
    out = dict(tokenizers=[dict(name=t.name, year=t.year, vocab=t.vocab) for t in toks], languages=list(LANGS.values()))

    # 1. Tokens for the same document in every language
    counts = {LANGS[c]: {t.name: t.count(s) for t in toks} for c, s in texts.items()}
    out["tokens"] = counts
    out["chars"] = {LANGS[c]: len(s) for c, s in texts.items()}
    out["bytes"] = {LANGS[c]: len(s.encode()) for c, s in texts.items()}
    out["words"] = {LANGS[c]: len(WORD.findall(s)) for c, s in texts.items()}
    out["parity"] = {l: {n: v / counts["English"][n] for n, v in d.items()} for l, d in counts.items()}

    # 2. Tokens per word (fertility) and its distribution, Arabic vs English
    hist = {}
    for lang, code in (("Arabic", "arb"), ("English", "eng")):
        words = WORD.findall(texts[code])
        hist[lang] = {}
        for t in toks:
            c = Counter(min(len(t.encode(" " + w)), 6) for w in words)
            hist[lang][t.name] = {str(k): c.get(k, 0) / len(words) for k in range(1, 7)}
    out["fertility_hist"] = hist
    out["fertility"] = {l: {n: counts[l][n] / out["words"][l] for n in counts[l]} for l in ("Arabic", "English", "Persian", "Turkish", "Hebrew", "Kurdish (Sorani)")}

    # 3. Share of each vocabulary that contains Arabic script
    share = {}
    for t in toks:
        n = 0
        for i in range(t.vocab):
            try:
                piece = t.decode_piece(i).decode("utf8", "ignore")
            except Exception:
                continue
            if ARABIC.search(piece):
                n += 1
        share[t.name] = n / t.vocab
    out["arabic_vocab_share"] = share

    # 4. Digits: Western 0-9 against Eastern Arabic ٠-٩
    nums = [str(x) for x in (7, 42, 2026, 13579, 1000000, 3.14159, 250000, 19.99, 1948, 911)]
    w = " ".join(nums)
    e = w.translate(EASTERN).replace(".", "٫")
    out["digits"] = {t.name: dict(western=t.count(w), eastern=t.count(e)) for t in toks}
    out["digits_text"] = dict(western=w, eastern=e)

    # 3b. Vocabulary by writing system
    scripts = {"Latin": r"\p{Latin}", "Cyrillic": r"\p{Cyrillic}", "Arabic": r"\p{Arabic}", "CJK": r"[\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}]",
               "Indic": r"[\p{Devanagari}\p{Bengali}\p{Tamil}\p{Telugu}\p{Gujarati}\p{Gurmukhi}\p{Kannada}\p{Malayalam}]"}
    comp = {}
    for t in toks:
        c = Counter()
        for i in range(t.vocab):
            try:
                p = t.decode_piece(i).decode("utf8", "ignore")
            except Exception:
                p = ""
            for k, pat in scripts.items():
                if regex.search(pat, p):
                    c[k] += 1
                    break
            else:
                c["Other (digits, symbols, bytes)"] += 1
        comp[t.name] = {k: c[k] / t.vocab for k in list(scripts) + ["Other (digits, symbols, bytes)"]}
    out["vocab_scripts"] = comp

    # 6. Small parallel sample written for this project: English, Modern Standard Arabic, Iraqi Arabic
    sample = json.load(open(ROOT / "data_samples" / "dialect_sample.json", encoding="utf8"))
    out["dialect"] = {k: {t.name: sum(t.count(s[k]) for s in sample) for t in toks} for k in ("english", "msa", "iraqi")}
    out["dialect_sentences"] = len(sample)
    return out


if __name__ == "__main__":
    r = run()
    (ROOT / "results").mkdir(exist_ok=True)
    json.dump(r, open(ROOT / "results" / "measurements.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for t in r["tokenizers"]:
        n = t["name"]
        print(f"{n:22s} dialect en/msa/iq {r['dialect']['english'][n]}/{r['dialect']['msa'][n]}/{r['dialect']['iraqi'][n]}  fert ar {r['fertility']['Arabic'][n]:.2f} en {r['fertility']['English'][n]:.2f}  AR/EN {r['parity']['Arabic'][n]:.2f}  vocab arabic share {100 * r['arabic_vocab_share'][n]:.2f}%  digits {r['digits'][n]}")
