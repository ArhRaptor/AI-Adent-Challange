import json
import math
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIG
# ============================================================

INDEX_FILE = Path("indexes/index_structured.json")

DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "chat_history.json"
TASK_STATE_FILE = DATA_DIR / "task_state.json"

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768

LLM_MODEL = "gemini-3.5-flash-lite"

TOP_K_BEFORE_FILTER = 8
TOP_K_AFTER_FILTER = 4

SIMILARITY_THRESHOLD = 0.45

HISTORY_WINDOW = 8


# ============================================================
# GEMINI
# ============================================================

client = genai.Client()


# ============================================================
# JSON STORAGE
# ============================================================

def load_json(
    path: Path,
    default
):
    if not path.exists():
        return default

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):
        return default


def save_json(
    path: Path,
    data
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# HISTORY
# ============================================================

def load_history() -> list[dict]:

    return load_json(
        HISTORY_FILE,
        []
    )


def save_history(
    history: list[dict]
):

    save_json(
        HISTORY_FILE,
        history
    )


def add_message(
    history: list[dict],
    role: str,
    content: str
):

    history.append(
        {
            "role": role,
            "content": content
        }
    )


def format_history(
    history: list[dict]
) -> str:

    recent = history[
        -HISTORY_WINDOW:
    ]

    if not recent:
        return "(история пока пуста)"

    parts = []

    for message in recent:

        role = message.get(
            "role",
            "unknown"
        )

        content = message.get(
            "content",
            ""
        )

        parts.append(
            f"{role.upper()}: "
            f"{content}"
        )

    return "\n".join(parts)


# ============================================================
# TASK STATE
# ============================================================

def default_task_state() -> dict:

    return {
        "goal": "",
        "clarifications": [],
        "constraints": [],
        "terms": {}
    }


def load_task_state() -> dict:

    state = load_json(
        TASK_STATE_FILE,
        default_task_state()
    )

    default = default_task_state()

    for key, value in default.items():

        if key not in state:
            state[key] = value

    return state


def save_task_state(
    state: dict
):

    save_json(
        TASK_STATE_FILE,
        state
    )


def format_task_state(
    state: dict
) -> str:

    return json.dumps(
        state,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# TASK MEMORY UPDATE
# ============================================================

def update_task_state(
    user_message: str,
    history: list[dict],
    current_state: dict
) -> dict:

    history_text = format_history(
        history
    )

    state_text = format_task_state(
        current_state
    )

    prompt = f"""
Ты обновляешь рабочую память
текущего диалога.

CURRENT TASK STATE:

{state_text}

RECENT HISTORY:

{history_text}

NEW USER MESSAGE:

{user_message}

Обнови task state.

Храни только информацию,
полезную для продолжения
текущей задачи.

Поля:

goal:
главная текущая цель пользователя.

clarifications:
что пользователь уже уточнил
по текущей задаче.

constraints:
зафиксированные ограничения
и требования.

terms:
важные термины и их значение
в рамках текущего диалога.

Правила:

- не придумывай факты;
- сохраняй старую информацию,
  если пользователь её не изменил;
- если пользователь явно изменил
  требование, используй новое;
- не записывай случайную беседу;
- не сохраняй полный transcript;
- не добавляй чувствительные данные;
- возвращай только JSON.

Формат:

{{
  "goal": "...",
  "clarifications": [
    "..."
  ],
  "constraints": [
    "..."
  ],
  "terms": {{
    "term": "meaning"
  }}
}}
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

    try:
        updated = json.loads(
            response.text
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):
        return current_state

    return {
        "goal": updated.get(
            "goal",
            current_state.get(
                "goal",
                ""
            )
        ),
        "clarifications":
            updated.get(
                "clarifications",
                current_state.get(
                    "clarifications",
                    []
                )
            ),
        "constraints":
            updated.get(
                "constraints",
                current_state.get(
                    "constraints",
                    []
                )
            ),
        "terms":
            updated.get(
                "terms",
                current_state.get(
                    "terms",
                    {}
                )
            )
    }


# ============================================================
# INDEX
# ============================================================

def load_index() -> dict:

    if not INDEX_FILE.exists():

        raise FileNotFoundError(
            f"Индекс не найден: "
            f"{INDEX_FILE}\n"
            "Запустите: "
            "py index_documents.py"
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
# CONTEXTUAL QUERY REWRITE
# ============================================================

def rewrite_query(
    question: str,
    history: list[dict],
    task_state: dict
) -> str:

    history_text = format_history(
        history
    )

    state_text = format_task_state(
        task_state
    )

    prompt = f"""
Создай короткий самостоятельный
поисковый запрос для semantic search.

Пользователь может использовать
слова вроде:

"это"
"он"
"такой подход"
"а что с этим?"
"а какие у него недостатки?"

Используй RECENT HISTORY
и TASK STATE, чтобы восстановить
контекст таких ссылок.

Не отвечай на вопрос.

Не добавляй фактов,
которых нет в сообщении,
истории или task state.

TASK STATE:

{state_text}

RECENT HISTORY:

{history_text}

CURRENT QUESTION:

{question}

Верни только поисковый запрос.
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
    index: dict
) -> list[dict]:

    query_embedding = (
        create_query_embedding(
            query
        )
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

    return results[
        :TOP_K_BEFORE_FILTER
    ]


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
# RAG CONTEXT
# ============================================================

def build_rag_context(
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
# CHAT ANSWER
# ============================================================

def generate_answer(
    question: str,
    history: list[dict],
    task_state: dict,
    chunks: list[dict]
) -> dict:

    if not chunks:

        return {
            "status": "unknown",
            "answer": (
                "Не знаю. В локальной "
                "базе недостаточно "
                "релевантной информации. "
                "Пожалуйста, уточните вопрос."
            ),
            "sources": []
        }

    history_text = format_history(
        history
    )

    state_text = format_task_state(
        task_state
    )

    rag_context = build_rag_context(
        chunks
    )

    prompt = f"""
Ты — ассистент в продолжительном
техническом диалоге.

Тебе доступны три разных вида
контекста:

1. TASK STATE
   Главная цель, уточнения,
   ограничения и термины.

2. RECENT HISTORY
   Последние сообщения диалога.

3. RAG CONTEXT
   Фактическая информация
   из локальных документов.

Правила:

- отвечай на CURRENT QUESTION;
- учитывай цель диалога;
- учитывай ранее зафиксированные
  ограничения;
- фактические утверждения о базе
  делай только на основе
  RAG CONTEXT;
- не придумывай источники;
- используй только chunk_id,
  реально переданные в
  RAG CONTEXT;
- обязательно верни sources;
- если данных недостаточно,
  скажи об этом;
- не считай историю диалога
  доказательством фактов
  из документов.

TASK STATE:

{state_text}

RECENT HISTORY:

{history_text}

RAG CONTEXT:

{rag_context}

CURRENT QUESTION:

{question}

Верни только JSON:

{{
  "status": "answered",
  "answer": "...",
  "sources": [
    {{
      "source": "...",
      "section": "...",
      "chunk_id": "..."
    }}
  ]
}}
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

    try:
        return json.loads(
            response.text
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return {
            "status": "error",
            "answer": (
                "Не удалось получить "
                "структурированный ответ."
            ),
            "sources": []
        }


# ============================================================
# SOURCE VALIDATION
# ============================================================

def validate_sources(
    result: dict,
    chunks: list[dict]
) -> dict:

    if result.get(
        "status"
    ) == "unknown":

        return {
            "valid": True,
            "errors": []
        }

    errors = []

    sources = result.get(
        "sources",
        []
    )

    if not sources:

        errors.append(
            "В ответе отсутствуют "
            "источники."
        )

    chunk_map = {
        chunk["metadata"].get(
            "chunk_id"
        ): chunk
        for chunk in chunks
    }

    for source in sources:

        chunk_id = source.get(
            "chunk_id"
        )

        if chunk_id not in chunk_map:

            errors.append(
                f"Неизвестный chunk_id: "
                f"{chunk_id}"
            )

            continue

        metadata = (
            chunk_map[
                chunk_id
            ]["metadata"]
        )

        if (
            source.get("source")
            != metadata.get("source")
        ):

            errors.append(
                f"Неверный source: "
                f"{chunk_id}"
            )

        if (
            source.get("section")
            != metadata.get("section")
        ):

            errors.append(
                f"Неверный section: "
                f"{chunk_id}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ============================================================
# PRINT
# ============================================================

def print_sources(
    result: dict
):

    sources = result.get(
        "sources",
        []
    )

    print()
    print("Источники:")

    if not sources:

        print("  Нет.")
        return

    for number, source in enumerate(
        sources,
        start=1
    ):

        print(
            f"  {number}. "
            f"{source.get('source')}"
        )

        print(
            f"     Section: "
            f"{source.get('section')}"
        )

        print(
            f"     Chunk ID: "
            f"{source.get('chunk_id')}"
        )


def print_task_state(
    task_state: dict
):

    print()
    print("=" * 60)
    print("TASK STATE")
    print("=" * 60)

    print(
        json.dumps(
            task_state,
            ensure_ascii=False,
            indent=2
        )
    )


# ============================================================
# HELP
# ============================================================

def print_help():

    print()
    print("Команды:")
    print(
        "  /help   - показать команды"
    )
    print(
        "  /state  - показать task state"
    )
    print(
        "  /history - показать историю"
    )
    print(
        "  /clear  - очистить чат и state"
    )
    print(
        "  /exit   - завершить работу"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "ДЕНЬ 25 — MINI RAG CHAT "
        "+ TASK MEMORY"
    )
    print("=" * 60)

    try:
        index = load_index()

    except FileNotFoundError as error:

        print(error)
        return

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    history = load_history()
    task_state = load_task_state()

    print()
    print(
        f"Index chunks: "
        f"{len(index['chunks'])}"
    )

    print(
        f"History messages: "
        f"{len(history)}"
    )

    print()
    print(
        "Введите /help "
        "для списка команд."
    )

    # ========================================================
    # CHAT LOOP
    # ========================================================

    while True:

        print()

        user_message = input(
            "Вы: "
        ).strip()

        if not user_message:
            continue

        # ----------------------------------------------------
        # COMMANDS
        # ----------------------------------------------------

        if user_message == "/exit":

            print(
                "Чат завершён."
            )
            break

        if user_message == "/help":

            print_help()
            continue

        if user_message == "/state":

            print_task_state(
                task_state
            )
            continue

        if user_message == "/history":

            print()
            print(
                format_history(
                    history
                )
            )

            continue

        if user_message == "/clear":

            history = []
            task_state = (
                default_task_state()
            )

            save_history(
                history
            )

            save_task_state(
                task_state
            )

            print(
                "История и task state "
                "очищены."
            )

            continue

        # ----------------------------------------------------
        # UPDATE TASK MEMORY
        # ----------------------------------------------------

        task_state = update_task_state(
            user_message=user_message,
            history=history,
            current_state=task_state
        )

        save_task_state(
            task_state
        )

        # ----------------------------------------------------
        # CONTEXTUAL QUERY
        # ----------------------------------------------------

        rewritten_query = (
            rewrite_query(
                question=user_message,
                history=history,
                task_state=task_state
            )
        )

        # ----------------------------------------------------
        # RAG
        # ----------------------------------------------------

        candidates = search_chunks(
            query=rewritten_query,
            index=index
        )

        chunks = filter_chunks(
            candidates
        )

        # ----------------------------------------------------
        # ANSWER
        # ----------------------------------------------------

        result = generate_answer(
            question=user_message,
            history=history,
            task_state=task_state,
            chunks=chunks
        )

        validation = (
            validate_sources(
                result,
                chunks
            )
        )

        # ----------------------------------------------------
        # PRINT
        # ----------------------------------------------------

        print()
        print(
            f"Поисковый запрос: "
            f"{rewritten_query}"
        )

        print()
        print(
            f"Найдено chunks: "
            f"{len(chunks)}"
        )

        print()
        print(
            "Ассистент:"
        )

        print(
            result.get(
                "answer",
                ""
            )
        )

        print_sources(
            result
        )

        if not validation["valid"]:

            print()
            print(
                "Ошибка проверки "
                "источников:"
            )

            for error in (
                validation["errors"]
            ):

                print(
                    f"  - {error}"
                )

        # ----------------------------------------------------
        # SAVE HISTORY
        # ----------------------------------------------------

        add_message(
            history,
            "user",
            user_message
        )

        add_message(
            history,
            "assistant",
            result.get(
                "answer",
                ""
            )
        )

        save_history(
            history
        )


if __name__ == "__main__":
    main()