"""Downloads the tokenizer files and the parallel text into data/.

Tokenizer files keep their own licenses (Llama community license, Gemma terms,
MIT for Whisper). They are fetched from their official GitHub repositories or
pip packages and are not redistributed here.
"""
import io, pathlib, shutil, subprocess, sys, tarfile, tempfile, urllib.request, zipfile

DATA = pathlib.Path("data")
DATA.mkdir(exist_ok=True)
FILES = {
    "llama3.model": "https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3/tokenizer.model",
    "llama4.model": "https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama4/tokenizer.model",
    "gemma.model": "https://raw.githubusercontent.com/google/gemma_pytorch/main/tokenizer/tokenizer.model",
    "gemma3.model": "https://raw.githubusercontent.com/google/gemma_pytorch/main/tokenizer/gemma3_cleaned_262144_v2.spiece.model",
}
for name, url in FILES.items():
    if not (DATA / name).exists():
        print("downloading", name)
        urllib.request.urlretrieve(url, DATA / name)
if not (DATA / "udhr2").exists():
    print("downloading the Universal Declaration of Human Rights corpus (NLTK udhr2)")
    raw = urllib.request.urlopen("https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/udhr2.zip").read()
    zipfile.ZipFile(io.BytesIO(raw)).extractall(DATA)
if not (DATA / "multilingual.tiktoken").exists():
    tmp = pathlib.Path(tempfile.mkdtemp())
    subprocess.run([sys.executable, "-m", "pip", "download", "openai-whisper==20250625", "--no-deps", "--no-binary", ":all:", "-d", str(tmp)], check=True)
    with tarfile.open(next(tmp.glob("*.tar.gz"))) as t:
        for m in t.getmembers():
            if m.name.endswith(("assets/gpt2.tiktoken", "assets/multilingual.tiktoken")):
                (DATA / pathlib.Path(m.name).name).write_bytes(t.extractfile(m).read())
print("done")
