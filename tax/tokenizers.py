"""Loads 7 open tokenizers. Files are downloaded by download.py, not stored in this repository."""
import base64, pathlib
import tiktoken

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
GPT2_PAT = r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
LLAMA3_PAT = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
O200K_PAT = r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n/]*|\s*[\r\n]+|\s+(?!\S)|\s+"""


def _ranks(path):
    out = {}
    for line in open(path, "rb").read().splitlines():
        if line:
            tok, rank = line.split()
            out[base64.b64decode(tok)] = int(rank)
    return out


class Tok:
    def __init__(self, name, year, encode, vocab, decode_piece):
        self.name, self.year, self.encode, self.vocab, self.decode_piece = name, year, encode, vocab, decode_piece

    def count(self, text):
        return len(self.encode(text))


def _tiktoken(name, year, file, pat):
    r = _ranks(DATA / file)
    enc = tiktoken.Encoding(name=name, pat_str=pat, mergeable_ranks=r, special_tokens={})
    inv = {v: k for k, v in r.items()}
    return Tok(name, year, lambda t: enc.encode_ordinary(t), len(r), lambda i: inv[i])


def _spm(name, year, file):
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor(model_file=str(DATA / file))
    return Tok(name, year, lambda t: sp.encode(t), sp.get_piece_size(), lambda i: sp.id_to_piece(i).replace("▁", " ").encode("utf8", "replace"))


def _tekken(name, year, file):
    import mistral_common, os
    from mistral_common.tokens.tokenizers.tekken import Tekkenizer
    path = pathlib.Path(os.path.dirname(mistral_common.__file__)) / "data" / file
    tk = Tekkenizer.from_file(str(path))
    n = tk.n_words - tk.num_special_tokens

    def piece(i):
        try:
            return tk.id_to_byte_piece(i + tk.num_special_tokens)
        except TypeError:
            return tk.id_to_byte_piece(i + tk.num_special_tokens, None)
    return Tok(name, year, lambda t: tk.encode(t, bos=False, eos=False), n, piece)


def load_all():
    return [
        _tiktoken("GPT-2", 2019, "gpt2.tiktoken", GPT2_PAT),
        _tiktoken("Whisper multilingual", 2022, "multilingual.tiktoken", GPT2_PAT),
        _spm("Gemma", 2024, "gemma.model"),
        _tiktoken("Llama 3", 2024, "llama3.model", LLAMA3_PAT),
        _tekken("Mistral Tekken", 2024, "tekken_240911.json"),
        _spm("Gemma 3", 2025, "gemma3.model"),
        _tiktoken("Llama 4", 2025, "llama4.model", O200K_PAT),
    ]
