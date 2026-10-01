import json
import re
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIG
# ============================================================

DOCUMENTS_DIR = Path("documents")
INDEX_DIR = Path("indexes")

FIXED_INDEX_FILE = INDEX_DIR / "index_fixed.json"
STRUCTURED_INDEX_FILE = INDEX_DIR / "index_structured.json"

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768

FIXED_CHUNK_SIZE = 1000
FIXED_CHUNK_OVERLAP = 200

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".kt",
    ".java",
    ".json",
}


# ============================================================
# GEMINI
# ============================================================

client = genai.Client()


# ============================================================
# DOCUMENT LOADING
# ============================================================

def load_documents() -> list[dict]:

    documents = []

    if not DOCUMENTS_DIR.exists():
        print(
            f"Каталог {DOCUMENTS_DIR} не найден."
        )
        return documents

    for path in sorted(
        DOCUMENTS_DIR.rglob("*")
    ):

        if not path.is_file():
            continue

        if (
            path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        try:

            text = path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:

            print(
                f"Пропущен файл "
                f"с неизвестной кодировкой: "
                f"{path}"
            )

            continue

        text = text.strip()

        if not text:
            continue

        documents.append(
            {
                "source": str(path),
                "title": path.name,
                "text": text
            }
        )

    return documents


# ============================================================
# FIXED CHUNKING
# ============================================================

def fixed_chunking(
    document: dict,
    chunk_size: int,
    overlap: int
) -> list[dict]:

    text = document["text"]

    chunks = []

    start = 0
    chunk_number = 0

    while start < len(text):

        end = start + chunk_size

        chunk_text = text[
            start:end
        ].strip()

        if chunk_text:

            chunk_id = (
                f"{document['title']}"
                f"::fixed::"
                f"{chunk_number:04d}"
            )

            chunks.append(
                {
                    "text": chunk_text,

                    "metadata": {
                        "source":
                            document["source"],

                        "title":
                            document["title"],

                        "section":
                            None,

                        "chunk_id":
                            chunk_id,

                        "strategy":
                            "fixed",

                        "start_char":
                            start,

                        "end_char":
                            min(
                                end,
                                len(text)
                            )
                    }
                }
            )

            chunk_number += 1

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# ============================================================
# STRUCTURED CHUNKING
# ============================================================

def detect_sections(
    document: dict
) -> list[dict]:

    text = document["text"]

    suffix = Path(
        document["source"]
    ).suffix.lower()

    # --------------------------------------------------------
    # Markdown
    # --------------------------------------------------------

    if suffix == ".md":

        pattern = re.compile(
            r"(?m)^(#{1,6})\s+(.+)$"
        )

        matches = list(
            pattern.finditer(text)
        )

        if not matches:

            return [
                {
                    "section":
                        document["title"],
                    "text":
                        text
                }
            ]

        sections = []

        # Текст до первого заголовка
        if matches[0].start() > 0:

            intro = text[
                :matches[0].start()
            ].strip()

            if intro:

                sections.append(
                    {
                        "section":
                            "Introduction",
                        "text":
                            intro
                    }
                )

        for index, match in enumerate(
            matches
        ):

            title = (
                match.group(2).strip()
            )

            start = match.start()

            if (
                index + 1
                < len(matches)
            ):

                end = matches[
                    index + 1
                ].start()

            else:
                end = len(text)

            section_text = text[
                start:end
            ].strip()

            if section_text:

                sections.append(
                    {
                        "section":
                            title,
                        "text":
                            section_text
                    }
                )

        return sections

    # --------------------------------------------------------
    # Python
    # --------------------------------------------------------

    if suffix == ".py":

        pattern = re.compile(
            r"(?m)^"
            r"(?:async\s+def|def|class)"
            r"\s+([A-Za-z_]"
            r"[A-Za-z0-9_]*)"
        )

        matches = list(
            pattern.finditer(text)
        )

        if matches:

            sections = []

            if matches[0].start() > 0:

                header = text[
                    :matches[0].start()
                ].strip()

                if header:

                    sections.append(
                        {
                            "section":
                                "module",
                            "text":
                                header
                        }
                    )

            for index, match in enumerate(
                matches
            ):

                start = match.start()

                if (
                    index + 1
                    < len(matches)
                ):

                    end = matches[
                        index + 1
                    ].start()

                else:
                    end = len(text)

                section_text = text[
                    start:end
                ].strip()

                if section_text:

                    sections.append(
                        {
                            "section":
                                match.group(1),
                            "text":
                                section_text
                        }
                    )

            return sections

    # --------------------------------------------------------
    # Other files
    # --------------------------------------------------------

    return [
        {
            "section":
                document["title"],

            "text":
                text
        }
    ]


def structured_chunking(
    document: dict
) -> list[dict]:

    sections = detect_sections(
        document
    )

    chunks = []

    chunk_number = 0

    for section in sections:

        section_text = (
            section["text"].strip()
        )

        if not section_text:
            continue

        # Очень большие разделы всё равно
        # необходимо ограничить по размеру.

        if (
            len(section_text)
            <= FIXED_CHUNK_SIZE
        ):

            pieces = [
                section_text
            ]

        else:

            pieces = []

            start = 0

            while (
                start
                < len(section_text)
            ):

                end = (
                    start
                    + FIXED_CHUNK_SIZE
                )

                piece = section_text[
                    start:end
                ].strip()

                if piece:
                    pieces.append(piece)

                if (
                    end
                    >= len(section_text)
                ):
                    break

                start = (
                    end
                    - FIXED_CHUNK_OVERLAP
                )

        for piece in pieces:

            chunk_id = (
                f"{document['title']}"
                f"::structured::"
                f"{chunk_number:04d}"
            )

            chunks.append(
                {
                    "text": piece,

                    "metadata": {
                        "source":
                            document["source"],

                        "title":
                            document["title"],

                        "section":
                            section["section"],

                        "chunk_id":
                            chunk_id,

                        "strategy":
                            "structured"
                    }
                }
            )

            chunk_number += 1

    return chunks


# ============================================================
# EMBEDDINGS
# ============================================================

def create_embedding(
    text: str
) -> list[float]:

    result = (
        client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=
                types.EmbedContentConfig(
                    output_dimensionality=
                        EMBEDDING_DIMENSIONS
                )
        )
    )

    return list(
        result.embeddings[0].values
    )


# ============================================================
# INDEX
# ============================================================

def build_index(
    chunks: list[dict],
    strategy: str
) -> dict:

    indexed_chunks = []

    total = len(chunks)

    print()
    print(
        f"Создание embeddings: "
        f"{strategy}"
    )

    print(
        f"Количество chunks: {total}"
    )

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print(
            f"[{index}/{total}] "
            f"{chunk['metadata']['chunk_id']}"
        )

        embedding = create_embedding(
            chunk["text"]
        )

        indexed_chunks.append(
            {
                "text":
                    chunk["text"],

                "metadata":
                    chunk["metadata"],

                "embedding":
                    embedding
            }
        )

    return {
        "strategy": strategy,
        "embedding_model":
            EMBEDDING_MODEL,
        "embedding_dimensions":
            EMBEDDING_DIMENSIONS,
        "chunks_count":
            len(indexed_chunks),
        "chunks":
            indexed_chunks
    }


# ============================================================
# SAVE
# ============================================================

def save_index(
    index: dict,
    path: Path
):

    INDEX_DIR.mkdir(
        exist_ok=True
    )

    path.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Индекс сохранён: {path}"
    )


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(
    documents,
    fixed_chunks,
    structured_chunks
):

    total_characters = sum(
        len(document["text"])
        for document in documents
    )

    # Очень грубая оценка страницы:
    # около 1800 символов текста.

    estimated_pages = (
        total_characters / 1800
    )

    print()
    print("=" * 60)
    print("СТАТИСТИКА")
    print("=" * 60)

    print(
        f"Документов: "
        f"{len(documents)}"
    )

    print(
        f"Символов: "
        f"{total_characters}"
    )

    print(
        f"Примерный объём: "
        f"{estimated_pages:.1f} страниц"
    )

    print()

    print(
        "Fixed chunks: "
        f"{len(fixed_chunks)}"
    )

    print(
        "Structured chunks: "
        f"{len(structured_chunks)}"
    )

    if fixed_chunks:

        fixed_average = sum(
            len(chunk["text"])
            for chunk in fixed_chunks
        ) / len(fixed_chunks)

        print(
            "Средний fixed chunk: "
            f"{fixed_average:.0f} символов"
        )

    if structured_chunks:

        structured_average = sum(
            len(chunk["text"])
            for chunk
            in structured_chunks
        ) / len(
            structured_chunks
        )

        print(
            "Средний structured chunk: "
            f"{structured_average:.0f} "
            f"символов"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "ДЕНЬ 21 — ИНДЕКСАЦИЯ ДОКУМЕНТОВ"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    documents = load_documents()

    if not documents:

        print(
            "Нет документов для "
            "индексации."
        )

        return

    print()
    print(
        f"Загружено документов: "
        f"{len(documents)}"
    )

    for document in documents:

        print(
            f"- {document['source']} "
            f"({len(document['text'])} "
            f"символов)"
        )

    # --------------------------------------------------------
    # FIXED CHUNKING
    # --------------------------------------------------------

    fixed_chunks = []

    for document in documents:

        fixed_chunks.extend(
            fixed_chunking(
                document,
                FIXED_CHUNK_SIZE,
                FIXED_CHUNK_OVERLAP
            )
        )

    # --------------------------------------------------------
    # STRUCTURED CHUNKING
    # --------------------------------------------------------

    structured_chunks = []

    for document in documents:

        structured_chunks.extend(
            structured_chunking(
                document
            )
        )

    # --------------------------------------------------------
    # COMPARE
    # --------------------------------------------------------

    print_statistics(
        documents,
        fixed_chunks,
        structured_chunks
    )

    # --------------------------------------------------------
    # EMBEDDINGS + INDEX
    # --------------------------------------------------------

    fixed_index = build_index(
        fixed_chunks,
        "fixed"
    )

    save_index(
        fixed_index,
        FIXED_INDEX_FILE
    )

    structured_index = build_index(
        structured_chunks,
        "structured"
    )

    save_index(
        structured_index,
        STRUCTURED_INDEX_FILE
    )

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("INDEXING COMPLETED")
    print("=" * 60)

    print(
        f"Fixed index: "
        f"{FIXED_INDEX_FILE}"
    )

    print(
        f"Structured index: "
        f"{STRUCTURED_INDEX_FILE}"
    )


if __name__ == "__main__":
    main()