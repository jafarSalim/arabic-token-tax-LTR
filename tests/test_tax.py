import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
pytestmark = pytest.mark.skipif(not (DATA / "llama4.model").exists(), reason="run download.py first")


def test_all_tokenizers_load_and_count():
    from tax.tokenizers import load_all
    toks = load_all()
    assert len(toks) == 7
    for t in toks:
        assert t.count("Hello world") >= 2


def test_english_parity_is_one():
    from tax.measure import run
    r = run()
    assert all(abs(v - 1) < 1e-12 for v in r["parity"]["English"].values())
    assert r["parity"]["Arabic"]["GPT-2"] > r["parity"]["Arabic"]["Llama 4"] > 1


def test_eastern_digits_translation():
    from tax.measure import EASTERN
    assert "2026".translate(EASTERN) == "٢٠٢٦"
