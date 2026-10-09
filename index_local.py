import json
import urllib.request
from pathlib import Path


DOCUMENTS_DIR = Path("documents")
INDEX_DIR = Path("indexes")
INDEX_FILE = INDEX_DIR / "index_local.json"

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".kt",
    ".java",
    ".json",
}


def read_documents() -> list[dict]:
    documents = []

    for path in DOCUMENTS_DIR.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Пропуск файла: {path}")
            continue

        if not text.strip():
            continue

        documents.append({
            "source": path.as_posix(),
            "title": path.name,
            "text": text,
        })

    return documents


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    chunks = []

    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def create_embedding(text: str) -> list[float]:
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_EMBED_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=300,
    ) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["embeddings"][0]


def build_index() -> list[dict]:
    documents = read_documents()

    print(f"Документов найдено: {len(documents)}")

    index = []

    for document in documents:
        chunks = chunk_text(
            document["text"]
        )

        print()
        print(document["source"])
        print(f"Chunks: {len(chunks)}")

        for number, chunk in enumerate(
            chunks,
            start=1,
        ):
            print(
                f"  Embedding "
                f"{number}/{len(chunks)}"
            )

            embedding = create_embedding(chunk)

            index.append({
                "text": chunk,
                "metadata": {
                    "source": document["source"],
                    "title": document["title"],
                    "section": None,
                    "chunk_id": (
                        f"{document['title']}"
                        f"::local::{number:04d}"
                    ),
                    "strategy": "local-fixed",
                },
                "embedding": embedding,
            })

    return index


def save_index(index: list[dict]):
    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    INDEX_FILE.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main():
    print("=" * 70)
    print("DAY 28 — LOCAL RAG INDEXING")
    print("=" * 70)

    print()
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Documents: {DOCUMENTS_DIR}")
    print(f"Index: {INDEX_FILE}")

    print()

    index = build_index()

    save_index(index)

    print()
    print("=" * 70)
    print("INDEX CREATED")
    print("=" * 70)

    print(f"Chunks: {len(index)}")
    print(f"Saved: {INDEX_FILE}")

    if index:
        dimensions = len(
            index[0]["embedding"]
        )

        print(
            f"Embedding dimensions: "
            f"{dimensions}"
        )


if __name__ == "__main__":
    main()