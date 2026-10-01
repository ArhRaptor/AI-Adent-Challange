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

# Baseline Day 22
BASELINE_TOP_K = 4

# Day 23
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
            f"Сначала запустите: "
            f"py index_documents.py"
        )

    with INDEX_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# EMBEDDING
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
            "Размерности embeddings "
            "не совпадают."
        )

    dot_product = sum(
        a * b
        for a, b in zip(
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
# VECTOR SEARCH
# ============================================================

def search_chunks(
    query: str,
    index: dict,
    top_k: int
) -> list[dict]:

    query_embedding = (
        create_query_embedding(
            query
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
- добавь только термины,
  явно следующие из вопроса;
- верни только поисковый запрос.

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

    rewritten = (
        response.text or ""
    ).strip()

    # Безопасный fallback.
    if not rewritten:
        return question

    return rewritten


# ============================================================
# FILTER
# ============================================================

def filter_chunks(
    chunks: list[dict],
    threshold: float,
    top_k: int
) -> list[dict]:

    relevant = [
        chunk
        for chunk in chunks
        if chunk["score"] >= threshold
    ]

    return relevant[:top_k]


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

File:
{metadata.get("title")}

Section:
{metadata.get("section")}

Chunk ID:
{metadata.get("chunk_id")}

Similarity:
{chunk["score"]:.4f}

Text:
{chunk["text"]}
""".strip()
        )

    return "\n\n".join(parts)


# ============================================================
# ANSWER
# ============================================================

def answer_with_context(
    question: str,
    chunks: list[dict]
) -> str:

    if not chunks:

        return (
            "В локальной базе не найдено "
            "достаточно релевантной информации "
            "для ответа."
        )

    context = build_context(
        chunks
    )

    prompt = f"""
Ответь на QUESTION,
используя только информацию
из CONTEXT.

Не придумывай отсутствующие факты.

Если CONTEXT недостаточно,
прямо скажи об этом.

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
# PRINT CHUNKS
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
# BASELINE RAG — DAY 22
# ============================================================

def run_baseline_rag(
    question: str,
    index: dict
):

    chunks = search_chunks(
        query=question,
        index=index,
        top_k=BASELINE_TOP_K
    )

    print_chunks(
        "BASELINE — TOP CHUNKS",
        chunks
    )

    answer = answer_with_context(
        question,
        chunks
    )

    return answer, chunks


# ============================================================
# IMPROVED RAG — DAY 23
# ============================================================

def run_improved_rag(
    question: str,
    index: dict
):

    # --------------------------------------------------------
    # STEP 1 — QUERY REWRITE
    # --------------------------------------------------------

    rewritten_query = (
        rewrite_query(
            question
        )
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
    # STEP 2 — RETRIEVAL
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
    # STEP 3 — FILTER
    # --------------------------------------------------------

    filtered = filter_chunks(
        chunks=candidates,
        threshold=
            SIMILARITY_THRESHOLD,
        top_k=
            TOP_K_AFTER_FILTER
    )

    print_chunks(
        f"AFTER FILTER "
        f"(threshold="
        f"{SIMILARITY_THRESHOLD}, "
        f"max TOP-"
        f"{TOP_K_AFTER_FILTER})",
        filtered
    )

    # --------------------------------------------------------
    # STEP 4 — ANSWER
    # --------------------------------------------------------

    answer = answer_with_context(
        question,
        filtered
    )

    return (
        answer,
        rewritten_query,
        candidates,
        filtered
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "ДЕНЬ 23 — RERANKING "
        "И ФИЛЬТРАЦИЯ"
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

    print()
    print(
        "Настройки Day 23:"
    )

    print(
        f"TOP-K before filter: "
        f"{TOP_K_BEFORE_FILTER}"
    )

    print(
        f"Similarity threshold: "
        f"{SIMILARITY_THRESHOLD}"
    )

    print(
        f"TOP-K after filter: "
        f"{TOP_K_AFTER_FILTER}"
    )

    print()

    question = input(
        "Ваш вопрос: "
    ).strip()

    if not question:
        return

    # ========================================================
    # BASELINE
    # ========================================================

    print()
    print("#" * 60)
    print("MODE 1 — BASELINE RAG")
    print("#" * 60)

    baseline_answer, baseline_chunks = (
        run_baseline_rag(
            question,
            index
        )
    )

    print()
    print("=" * 60)
    print("BASELINE ANSWER")
    print("=" * 60)

    print()
    print(
        baseline_answer
    )

    # ========================================================
    # IMPROVED
    # ========================================================

    print()
    print("#" * 60)
    print("MODE 2 — IMPROVED RAG")
    print("#" * 60)

    (
        improved_answer,
        rewritten_query,
        candidates,
        filtered_chunks
    ) = run_improved_rag(
        question,
        index
    )

    print()
    print("=" * 60)
    print("IMPROVED ANSWER")
    print("=" * 60)

    print()
    print(
        improved_answer
    )

    # ========================================================
    # COMPARISON
    # ========================================================

    print()
    print("=" * 60)
    print("СРАВНЕНИЕ")
    print("=" * 60)

    print()

    print(
        f"Baseline chunks: "
        f"{len(baseline_chunks)}"
    )

    print(
        f"Candidates before filter: "
        f"{len(candidates)}"
    )

    print(
        f"Chunks after filter: "
        f"{len(filtered_chunks)}"
    )

    removed = (
        len(candidates)
        - len(filtered_chunks)
    )

    print(
        f"Removed by filter: "
        f"{removed}"
    )

    print()
    print(
        "Day 23 completed."
    )


if __name__ == "__main__":
    main()