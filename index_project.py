"""Index README and docs locally using Ollama embeddings."""
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get('DAY31_PROJECT_ROOT', Path(__file__).resolve().parent)).resolve()
INDEX = ROOT / 'indexes' / 'day31_project.json'
OLLAMA = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
EMBED_MODEL = os.environ.get('DAY31_EMBED_MODEL', 'nomic-embed-text')


def post(path, data):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def embed(texts):
    data = post('/api/embed', {'model': EMBED_MODEL, 'input': texts})
    return data['embeddings']


def sources():
    paths = [ROOT / 'README.md']
    docs = ROOT / 'docs'
    if docs.exists():
        paths += sorted(p for p in docs.rglob('*') if p.is_file() and p.suffix.lower() in {'.md', '.txt', '.json', '.yaml', '.yml'} and len(p.relative_to(docs).parts) <= 5)
    return [p for p in paths if p.is_file() and p.stat().st_size <= 1024 * 1024]


def chunks(text, size=1100, overlap=180):
    if size <= overlap:
        raise ValueError('size must exceed overlap')
    start = 0
    while start < len(text):
        yield text[start:start + size]
        if start + size >= len(text):
            break
        start += size - overlap


def build():
    entries = []
    for file in sources():
        text = file.read_text(encoding='utf-8-sig', errors='replace')
        for n, chunk in enumerate(chunks(text)):
            if chunk.strip():
                entries.append({'source': str(file.relative_to(ROOT)).replace('\\', '/'), 'chunk': n, 'text': chunk})
    if not entries:
        raise RuntimeError('No documentation found. Add README.md or files under docs/.')
    for start in range(0, len(entries), 16):
        batch = entries[start:start + 16]
        vectors = embed([e['text'] for e in batch])
        for entry, vector in zip(batch, vectors):
            entry['embedding'] = vector
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({'model': EMBED_MODEL, 'entries': entries}, ensure_ascii=False), encoding='utf-8')
    print(f'Indexed {len(entries)} chunks from {len(set(e["source"] for e in entries))} files -> {INDEX}')


if __name__ == '__main__':
    build()
