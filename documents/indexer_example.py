from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ChunkMetadata:
    source: str
    title: str
    section: str | None
    chunk_id: str
    strategy: str


@dataclass
class Chunk:
    text: str
    metadata: ChunkMetadata


def discover_files(root: Path, extensions: set[str]) -> list[Path]:
    """Return supported files recursively."""
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    ]


def read_utf8(path: Path) -> str:
    """Read one UTF-8 text document."""
    return path.read_text(encoding="utf-8").strip()


def fixed_chunks(text: str, size: int = 1200, overlap: int = 200) -> Iterable[str]:
    """Yield overlapping fixed-size chunks."""
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")

    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end].strip()
        if piece:
            yield piece
        if end >= len(text):
            break
        start = end - overlap


def make_chunk_id(filename: str, strategy: str, number: int) -> str:
    """Build a stable readable identifier."""
    return f"{filename}::{strategy}::{number:04d}"


class DocumentIndexer:
    """Small example showing separation between loading, chunking and storage."""

    def __init__(self, root: Path):
        self.root = root
        self.extensions = {".md", ".txt", ".py", ".kt", ".java", ".json"}

    def load(self) -> list[tuple[Path, str]]:
        documents = []
        for path in discover_files(self.root, self.extensions):
            text = read_utf8(path)
            if text:
                documents.append((path, text))
        return documents

    def chunk(self, path: Path, text: str) -> list[Chunk]:
        result = []
        for number, piece in enumerate(fixed_chunks(text)):
            metadata = ChunkMetadata(
                source=str(path),
                title=path.name,
                section=None,
                chunk_id=make_chunk_id(path.name, "fixed", number),
                strategy="fixed",
            )
            result.append(Chunk(text=piece, metadata=metadata))
        return result

    def build(self) -> list[Chunk]:
        chunks = []
        for path, text in self.load():
            chunks.extend(self.chunk(path, text))
        return chunks


def validate_chunks(chunks: list[Chunk]) -> None:
    """Basic validation before embedding."""
    ids = set()
    for chunk in chunks:
        if not chunk.text:
            raise ValueError("empty chunk")
        if chunk.metadata.chunk_id in ids:
            raise ValueError("duplicate chunk id")
        ids.add(chunk.metadata.chunk_id)


def main() -> None:
    indexer = DocumentIndexer(Path("documents"))
    chunks = indexer.build()
    validate_chunks(chunks)
    print(f"Prepared chunks: {len(chunks)}")


if __name__ == "__main__":
    main()
