import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path


INDEX_FILE = Path(
    "indexes/index_local.json"
)

OLLAMA_EMBED_URL = (
    "http://localhost:11434/api/embed"
)

OLLAMA_CHAT_URL = (
    "http://localhost:11434/api/chat"
)

EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5-coder:0.5b"

TOP_K = 4


def post_json(
    url: str,
    payload: dict,
) -> dict:
    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
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
        return json.loads(
            response.read().decode("utf-8")
        )


def load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            "Локальный индекс не найден.\n"
            "Сначала запусти:\n"
            "py index_local.py"
        )

    return json.loads(
        INDEX_FILE.read_text(
            encoding="utf-8"
        )
    )


def create_embedding(
    text: str,
) -> list[float]:
    result = post_json(
        OLLAMA_EMBED_URL,
        {
            "model": EMBEDDING_MODEL,
            "input": text,
        },
    )

    return result["embeddings"][0]


def cosine_similarity(
    a: list[float],
    b: list[float],
) -> float:
    if len(a) != len(b):
        raise ValueError(
            "Embedding dimensions do not match."
        )

    dot_product = sum(
        x * y
        for x, y in zip(a, b)
    )

    norm_a = math.sqrt(
        sum(x * x for x in a)
    )

    norm_b = math.sqrt(
        sum(y * y for y in b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return (
        dot_product
        / (norm_a * norm_b)
    )


def retrieve(
    question: str,
    index: list[dict],
    top_k: int = TOP_K,
) -> list[dict]:
    query_embedding = create_embedding(
        question
    )

    scored = []

    for chunk in index:
        score = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        scored.append({
            "score": score,
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        })

    scored.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored[:top_k]


def build_context(
    chunks: list[dict],
) -> str:
    parts = []

    for number, chunk in enumerate(
        chunks,
        start=1,
    ):
        metadata = chunk["metadata"]

        parts.append(
            f"""
SOURCE {number}

File:
{metadata["source"]}

Chunk ID:
{metadata["chunk_id"]}

Similarity:
{chunk["score"]:.4f}

Text:
{chunk["text"]}
""".strip()
        )

    return "\n\n---\n\n".join(parts)


def generate_answer(
    question: str,
    chunks: list[dict],
) -> tuple[str, float]:
    context = build_context(chunks)

    system_prompt = """
You are a RAG assistant.

Answer the user's question using only
the provided LOCAL CONTEXT.

Rules:

1. Do not invent facts.
2. If the context is insufficient,
   say that you do not know.
3. Keep the answer concise.
4. Use the document context as
   the source of factual information.
""".strip()

    user_prompt = f"""
LOCAL CONTEXT:

{context}


QUESTION:

{question}
""".strip()

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "stream": False,
    }

    start = time.perf_counter()

    result = post_json(
        OLLAMA_CHAT_URL,
        payload,
    )

    elapsed = (
        time.perf_counter() - start
    )

    answer = (
        result["message"]["content"]
    )

    return answer, elapsed


def print_sources(
    chunks: list[dict],
):
    print()
    print("ИСТОЧНИКИ:")

    for number, chunk in enumerate(
        chunks,
        start=1,
    ):
        metadata = chunk["metadata"]

        print()
        print(
            f"[{number}] "
            f"{metadata['source']}"
        )
        print(
            f"    Chunk: "
            f"{metadata['chunk_id']}"
        )
        print(
            f"    Similarity: "
            f"{chunk['score']:.4f}"
        )


def main():
    print("=" * 70)
    print("DAY 28 — FULLY LOCAL RAG")
    print("=" * 70)

    print()
    print(
        f"Embedding model: "
        f"{EMBEDDING_MODEL}"
    )
    print(
        f"LLM: {LLM_MODEL}"
    )
    print(
        "Cloud LLM API: NONE"
    )

    try:
        index = load_index()
    except Exception as error:
        print()
        print(error)
        return

    print(
        f"Index chunks: {len(index)}"
    )

    while True:
        print()

        try:
            question = input(
                "Вопрос: "
            ).strip()
        except (
            KeyboardInterrupt,
            EOFError,
        ):
            print()
            break

        if not question:
            continue

        if question.lower() in {
            "/exit",
            "exit",
        }:
            break

        try:
            retrieval_start = (
                time.perf_counter()
            )

            chunks = retrieve(
                question,
                index,
            )

            retrieval_time = (
                time.perf_counter()
                - retrieval_start
            )

            answer, generation_time = (
                generate_answer(
                    question,
                    chunks,
                )
            )

        except urllib.error.URLError:
            print()
            print(
                "Не удалось подключиться "
                "к Ollama."
            )
            continue

        except Exception as error:
            print()
            print(f"Ошибка: {error}")
            continue

        print()
        print("LOCAL LLM:")
        print(answer)

        print_sources(chunks)

        print()
        print(
            "Retrieval: "
            f"{retrieval_time:.2f} сек."
        )

        print(
            "Generation: "
            f"{generation_time:.2f} сек."
        )

        print(
            "Total: "
            f"{retrieval_time + generation_time:.2f} сек."
        )


if __name__ == "__main__":
    main()