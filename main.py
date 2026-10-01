import json
import math
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIG
# ============================================================

INDEX_FILE = Path("indexes/index_structured.json")

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768

LLM_MODEL = "gemini-3.5-flash-lite"

TOP_K_BEFORE_FILTER = 8
TOP_K_AFTER_FILTER = 4

SIMILARITY_THRESHOLD = 0.45


# ============================================================
# GEMINI
# ============================================================

client = genai.Client()


# ============================================================
# LOAD INDEX
# ============================================================

def load_index() -> dict:

    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Индекс не найден: {INDEX_FILE}\n"
            "Сначала запустите: py index_documents.py"
        )

    with INDEX_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# QUERY EMBEDDING
# ============================================================

def create_query_embedding(
    query: str
) -> list[float]:

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            output_dimensionality=
                EMBEDDING_DIMENSIONS
        )
    )

    return list(
        result.embeddings[0].values
    )


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float]
) -> float:

    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Размерности embeddings не совпадают."
        )

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b
        )
    )

    norm_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    norm_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return (
        dot_product
        / (norm_a * norm_b)
    )


# ============================================================
# QUERY REWRITE
# ============================================================

def rewrite_query(
    question: str
) -> str:

    prompt = f"""
Перепиши вопрос пользователя
в короткий поисковый запрос
для semantic search по технической
базе документов.

Правила:

- сохрани исходный смысл;
- не отвечай на вопрос;
- не добавляй новые факты;
- убери разговорные слова;
- верни только поисковый запрос.

Вопрос:

{question}
""".strip()

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=
                types.ThinkingConfig(
                    thinking_level="minimal"
                )
        )
    )

    rewritten = (
        response.text or ""
    ).strip()

    return rewritten or question


# ============================================================
# SEARCH
# ============================================================

def search_chunks(
    query: str,
    index: dict,
    top_k: int
) -> list[dict]:

    query_embedding = (
        create_query_embedding(query)
    )

    results = []

    for chunk in index["chunks"]:

        score = cosine_similarity(
            query_embedding,
            chunk["embedding"]
        )

        results.append(
            {
                "score": score,
                "text": chunk["text"],
                "metadata":
                    chunk["metadata"]
            }
        )

    results.sort(
        key=lambda item:
            item["score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# FILTER
# ============================================================

def filter_chunks(
    chunks: list[dict]
) -> list[dict]:

    relevant = [
        chunk
        for chunk in chunks
        if chunk["score"]
        >= SIMILARITY_THRESHOLD
    ]

    return relevant[
        :TOP_K_AFTER_FILTER
    ]


# ============================================================
# CONTEXT
# ============================================================

def build_context(
    chunks: list[dict]
) -> str:

    parts = []

    for number, chunk in enumerate(
        chunks,
        start=1
    ):

        metadata = chunk["metadata"]

        parts.append(
            f"""
--- SOURCE {number} ---

source:
{metadata.get("source")}

title:
{metadata.get("title")}

section:
{metadata.get("section")}

chunk_id:
{metadata.get("chunk_id")}

similarity:
{chunk["score"]:.4f}

text:
{chunk["text"]}
""".strip()
        )

    return "\n\n".join(parts)


# ============================================================
# "I DON'T KNOW"
# ============================================================

def should_abstain(
    chunks: list[dict]
) -> bool:

    if not chunks:
        return True

    best_score = chunks[0]["score"]

    return (
        best_score
        < SIMILARITY_THRESHOLD
    )


def build_unknown_answer() -> dict:

    return {
        "status": "unknown",
        "answer": (
            "Не знаю. В локальной базе "
            "недостаточно релевантной информации. "
            "Пожалуйста, уточните вопрос."
        ),
        "sources": [],
        "quotes": []
    }


# ============================================================
# RAG ANSWER
# ============================================================

def generate_grounded_answer(
    question: str,
    chunks: list[dict]
) -> dict:

    context = build_context(chunks)

    prompt = f"""
Ответь на QUESTION,
используя ТОЛЬКО информацию
из CONTEXT.

Запрещено использовать факты,
которых нет в CONTEXT.

Каждое существенное утверждение
в answer должно подтверждаться
переданными chunks.

Ты обязан вернуть:

1. answer
2. sources
3. quotes

Для sources используй только
source, section и chunk_id,
которые реально присутствуют
в CONTEXT.

Для quotes копируй короткие
фрагменты ДОСЛОВНО из текста
соответствующего chunk.

Не придумывай цитаты.

Каждая quote должна содержать
chunk_id источника.

Верни только JSON следующего вида:

{{
  "status": "answered",
  "answer": "...",
  "sources": [
    {{
      "source": "...",
      "section": "...",
      "chunk_id": "..."
    }}
  ],
  "quotes": [
    {{
      "chunk_id": "...",
      "quote": "..."
    }}
  ]
}}

CONTEXT:

{context}

QUESTION:

{question}
""".strip()

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type=
                "application/json",
            thinking_config=
                types.ThinkingConfig(
                    thinking_level="minimal"
                )
        )
    )

    return json.loads(response.text)


# ============================================================
# VALIDATION
# ============================================================

def validate_answer(
    result: dict,
    chunks: list[dict]
) -> dict:

    errors = []

    if not result.get("answer"):
        errors.append(
            "Ответ отсутствует."
        )

    sources = result.get(
        "sources",
        []
    )

    quotes = result.get(
        "quotes",
        []
    )

    if not sources:
        errors.append(
            "Источники отсутствуют."
        )

    if not quotes:
        errors.append(
            "Цитаты отсутствуют."
        )

    # --------------------------------------------------------
    # Allowed chunks
    # --------------------------------------------------------

    chunk_map = {
        chunk["metadata"].get(
            "chunk_id"
        ): chunk
        for chunk in chunks
    }

    # --------------------------------------------------------
    # Validate sources
    # --------------------------------------------------------

    for source in sources:

        chunk_id = source.get(
            "chunk_id"
        )

        if chunk_id not in chunk_map:

            errors.append(
                f"Неизвестный source "
                f"chunk_id: {chunk_id}"
            )

            continue

        real_metadata = (
            chunk_map[
                chunk_id
            ]["metadata"]
        )

        if (
            source.get("source")
            != real_metadata.get("source")
        ):
            errors.append(
                f"Неверный source для "
                f"{chunk_id}"
            )

        if (
            source.get("section")
            != real_metadata.get("section")
        ):
            errors.append(
                f"Неверный section для "
                f"{chunk_id}"
            )

    # --------------------------------------------------------
    # Validate quotes
    # --------------------------------------------------------

    for quote_item in quotes:

        chunk_id = quote_item.get(
            "chunk_id"
        )

        quote = (
            quote_item.get(
                "quote",
                ""
            )
            .strip()
        )

        if chunk_id not in chunk_map:

            errors.append(
                f"Цитата с неизвестным "
                f"chunk_id: {chunk_id}"
            )

            continue

        original_text = (
            chunk_map[
                chunk_id
            ]["text"]
        )

        if not quote:

            errors.append(
                f"Пустая цитата: "
                f"{chunk_id}"
            )

            continue

        if quote not in original_text:

            errors.append(
                f"Цитата не найдена "
                f"дословно в chunk: "
                f"{chunk_id}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ============================================================
# PRINT RETRIEVAL
# ============================================================

def print_chunks(
    title: str,
    chunks: list[dict]
):

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    if not chunks:

        print()
        print(
            "Релевантные chunks "
            "не найдены."
        )

        return

    for number, chunk in enumerate(
        chunks,
        start=1
    ):

        metadata = chunk["metadata"]

        print()

        print(
            f"{number}. "
            f"{metadata.get('title')}"
        )

        print(
            f"   Section: "
            f"{metadata.get('section')}"
        )

        print(
            f"   Chunk ID: "
            f"{metadata.get('chunk_id')}"
        )

        print(
            f"   Similarity: "
            f"{chunk['score']:.4f}"
        )


# ============================================================
# PRINT ANSWER
# ============================================================

def print_answer(
    result: dict
):

    print()
    print("=" * 60)
    print("ОТВЕТ")
    print("=" * 60)

    print()
    print(
        result.get(
            "answer",
            ""
        )
    )

    sources = result.get(
        "sources",
        []
    )

    if sources:

        print()
        print("=" * 60)
        print("ИСТОЧНИКИ")
        print("=" * 60)

        for number, source in enumerate(
            sources,
            start=1
        ):

            print()

            print(
                f"{number}. "
                f"{source.get('source')}"
            )

            print(
                f"   Section: "
                f"{source.get('section')}"
            )

            print(
                f"   Chunk ID: "
                f"{source.get('chunk_id')}"
            )

    quotes = result.get(
        "quotes",
        []
    )

    if quotes:

        print()
        print("=" * 60)
        print("ЦИТАТЫ")
        print("=" * 60)

        for number, quote in enumerate(
            quotes,
            start=1
        ):

            print()

            print(
                f"{number}. "
                f"[{quote.get('chunk_id')}]"
            )

            print(
                f"   \""
                f"{quote.get('quote')}"
                f"\""
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "ДЕНЬ 24 — ЦИТАТЫ, "
        "ИСТОЧНИКИ И "
        "АНТИ-ГАЛЛЮЦИНАЦИИ"
    )
    print("=" * 60)

    try:
        index = load_index()

    except FileNotFoundError as error:

        print(error)
        return

    print()
    print(
        f"Index: {INDEX_FILE}"
    )

    print(
        f"Chunks: "
        f"{len(index['chunks'])}"
    )

    print(
        f"Threshold: "
        f"{SIMILARITY_THRESHOLD}"
    )

    print()

    question = input(
        "Ваш вопрос: "
    ).strip()

    if not question:
        return

    # --------------------------------------------------------
    # QUERY REWRITE
    # --------------------------------------------------------

    rewritten_query = (
        rewrite_query(question)
    )

    print()
    print("=" * 60)
    print("QUERY REWRITE")
    print("=" * 60)

    print()
    print(
        f"Original:\n"
        f"{question}"
    )

    print()
    print(
        f"Rewritten:\n"
        f"{rewritten_query}"
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    candidates = search_chunks(
        query=rewritten_query,
        index=index,
        top_k=
            TOP_K_BEFORE_FILTER
    )

    print_chunks(
        f"BEFORE FILTER "
        f"(TOP-{TOP_K_BEFORE_FILTER})",
        candidates
    )

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    filtered = filter_chunks(
        candidates
    )

    print_chunks(
        "AFTER FILTER",
        filtered
    )

    # --------------------------------------------------------
    # ANTI-HALLUCINATION GATE
    # --------------------------------------------------------

    if should_abstain(filtered):

        result = (
            build_unknown_answer()
        )

        print_answer(result)

        print()
        print("=" * 60)
        print("ANTI-HALLUCINATION")
        print("=" * 60)

        print()
        print(
            "Ответ LLM не генерировался, "
            "потому что релевантность "
            "контекста ниже порога."
        )

        return

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    result = (
        generate_grounded_answer(
            question,
            filtered
        )
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validation = validate_answer(
        result,
        filtered
    )

    print_answer(result)

    print()
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)

    print()

    print(
        f"Sources present: "
        f"{bool(result.get('sources'))}"
    )

    print(
        f"Quotes present: "
        f"{bool(result.get('quotes'))}"
    )

    print(
        f"Validation passed: "
        f"{validation['valid']}"
    )

    if validation["errors"]:

        print()

        for error in (
            validation["errors"]
        ):
            print(
                f"- {error}"
            )


if __name__ == "__main__":
    main()