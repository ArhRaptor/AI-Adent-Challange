import json
import math
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIG
# ============================================================

INDEX_FILE = Path(
    "indexes/index_structured.json"
)

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768

LLM_MODEL = "gemini-3.5-flash-lite"

TOP_K = 4


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
            f"Сначала запустите: "
            f"py index_documents.py"
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
    question: str
) -> list[float]:

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
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
            "Размерности embeddings "
            "не совпадают."
        )

    dot_product = sum(
        a * b
        for a, b
        in zip(
            vector_a,
            vector_b
        )
    )

    norm_a = math.sqrt(
        sum(
            a * a
            for a in vector_a
        )
    )

    norm_b = math.sqrt(
        sum(
            b * b
            for b in vector_b
        )
    )

    if (
        norm_a == 0
        or norm_b == 0
    ):
        return 0.0

    return (
        dot_product
        / (norm_a * norm_b)
    )


# ============================================================
# RETRIEVAL
# ============================================================

def search_chunks(
    question: str,
    index: dict,
    top_k: int = TOP_K
) -> list[dict]:

    query_embedding = (
        create_query_embedding(
            question
        )
    )

    scored_chunks = []

    for chunk in index["chunks"]:

        score = cosine_similarity(
            query_embedding,
            chunk["embedding"]
        )

        scored_chunks.append(
            {
                "score": score,
                "text": chunk["text"],
                "metadata":
                    chunk["metadata"]
            }
        )

    scored_chunks.sort(
        key=lambda item:
            item["score"],
        reverse=True
    )

    return scored_chunks[:top_k]


# ============================================================
# WITHOUT RAG
# ============================================================

def ask_without_rag(
    question: str
) -> str:

    prompt = f"""
Ответь на вопрос пользователя.

Не используй локальную базу документов.
Ответь только на основе собственных знаний.

Вопрос:

{question}
""".strip()

    response = (
        client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=
                types.GenerateContentConfig(
                    thinking_config=
                        types.ThinkingConfig(
                            thinking_level=
                                "minimal"
                        )
                )
        )
    )

    return response.text


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

        metadata = (
            chunk["metadata"]
        )

        part = f"""
--- SOURCE {number} ---

File:
{metadata.get("title")}

Section:
{metadata.get("section")}

Chunk ID:
{metadata.get("chunk_id")}

Text:
{chunk["text"]}
""".strip()

        parts.append(part)

    return "\n\n".join(parts)


# ============================================================
# WITH RAG
# ============================================================

def ask_with_rag(
    question: str,
    chunks: list[dict]
) -> str:

    context = build_context(
        chunks
    )

    prompt = f"""
Ты отвечаешь на вопрос,
используя локальную базу документов.

Используй только информацию,
которая содержится в CONTEXT.

Если в CONTEXT недостаточно информации,
прямо скажи об этом.

Не придумывай факты,
которых нет в переданных документах.

CONTEXT:

{context}

QUESTION:

{question}

ANSWER:
""".strip()

    response = (
        client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=
                types.GenerateContentConfig(
                    thinking_config=
                        types.ThinkingConfig(
                            thinking_level=
                                "minimal"
                        )
                )
        )
    )

    return response.text


# ============================================================
# PRINT SOURCES
# ============================================================

def print_sources(
    chunks: list[dict]
):

    print()
    print("=" * 60)
    print("НАЙДЕННЫЕ CHUNKS")
    print("=" * 60)

    for number, chunk in enumerate(
        chunks,
        start=1
    ):

        metadata = (
            chunk["metadata"]
        )

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
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "ДЕНЬ 22 — ПЕРВЫЙ RAG-ЗАПРОС"
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
        f"Embedding model: "
        f"{index['embedding_model']}"
    )

    print()

    question = input(
        "Ваш вопрос: "
    ).strip()

    if not question:
        return

    # --------------------------------------------------------
    # WITHOUT RAG
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("БЕЗ RAG")
    print("=" * 60)

    answer_without_rag = (
        ask_without_rag(
            question
        )
    )

    print()
    print(
        answer_without_rag
    )

    # --------------------------------------------------------
    # RETRIEVAL
    # --------------------------------------------------------

    chunks = search_chunks(
        question,
        index
    )

    print_sources(
        chunks
    )

    # --------------------------------------------------------
    # WITH RAG
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("С RAG")
    print("=" * 60)

    answer_with_rag = (
        ask_with_rag(
            question,
            chunks
        )
    )

    print()
    print(
        answer_with_rag
    )

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("СРАВНЕНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == "__main__":
    main()