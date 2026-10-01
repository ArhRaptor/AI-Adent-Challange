# День 22 — Первый RAG-запрос

## Цель

Реализовать первый полноценный RAG pipeline поверх локального индекса документов, созданного на Дне 21.

Система должна выполнять цепочку:

```text
Вопрос пользователя
        ↓
Embedding вопроса
        ↓
Поиск релевантных chunks
        ↓
Top-K chunks
        ↓
Контекст + вопрос
        ↓
LLM
        ↓
Ответ на основе локальных документов
```

Дополнительно реализовано сравнение двух режимов:

```text
WITHOUT RAG
vs
WITH RAG
```

и подготовлен набор из 10 контрольных вопросов для оценки качества retrieval и ответов.

---

# Что такое RAG

RAG — Retrieval-Augmented Generation.

Обычный LLM-запрос выглядит так:

```text
Question
   ↓
LLM
   ↓
Answer
```

Модель отвечает на основе собственных знаний.

RAG добавляет перед LLM этап поиска информации:

```text
Question
   ↓
Retrieval
   ↓
Relevant Documents
   ↓
Question + Context
   ↓
LLM
   ↓
Answer
```

Таким образом модель получает дополнительный контекст из нашей локальной базы документов.

---

# Связь с Днём 21

На Дне 21 был создан pipeline индексации:

```text
Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
Metadata
    ↓
Local Index
```

Результатом стал локальный индекс:

```text
indexes/index_structured.json
```

На Дне 22 этот индекс используется для поиска.

Получается полный pipeline:

```text
DAY 21

Documents
    ↓
Chunks
    ↓
Embeddings
    ↓
Index

=========================

DAY 22

Question
    ↓
Query Embedding
    ↓
Index Search
    ↓
Relevant Chunks
    ↓
LLM
    ↓
Answer
```

---

# Структура проекта

```text
.
├── main.py
├── index_documents.py
├── control_questions.json
├── README.md
│
├── documents/
│   ├── README.md
│   ├── rag_notes.md
│   ├── mcp_notes.md
│   ├── android_architecture.md
│   ├── agent_design.txt
│   ├── chunking_comparison.md
│   ├── python_services.md
│   ├── software_architecture.md
│   ├── indexer_example.py
│   ├── compose_example.kt
│   └── index_config_examples.json
│
└── indexes/
    ├── index_fixed.json
    └── index_structured.json
```

---

# index_documents.py

Файл содержит pipeline индексации из Дня 21.

Он выполняет:

```text
documents/
    ↓
load_documents()
    ↓
chunking
    ↓
embeddings
    ↓
local indexes
```

Если индекс ещё не создан:

```powershell
py index_documents.py
```

После выполнения появляются:

```text
indexes/index_fixed.json
indexes/index_structured.json
```

---

# main.py

Главный файл Дня 22.

Он реализует два режима:

```text
WITHOUT RAG
WITH RAG
```

Один пользовательский вопрос отправляется через оба pipeline, поэтому ответы можно сравнить непосредственно в консоли.

---

# Режим WITHOUT RAG

Первый режим отправляет вопрос непосредственно в LLM:

```text
Question
   ↓
Gemini
   ↓
Answer
```

Локальный индекс документов при генерации этого ответа не используется.

Функция:

```python
ask_without_rag()
```

позволяет получить baseline для сравнения.

---

# Режим WITH RAG

Второй режим выполняет полный retrieval pipeline:

```text
Question
   ↓
Query Embedding
   ↓
Cosine Similarity
   ↓
Top-K Chunks
   ↓
Build Context
   ↓
Context + Question
   ↓
Gemini
   ↓
RAG Answer
```

---

# Загрузка индекса

Для retrieval используется:

```text
indexes/index_structured.json
```

Индекс содержит:

```text
chunk text
+
metadata
+
embedding
```

Пример записи:

```json
{
  "text": "...",
  "metadata": {
    "source": "documents/rag_notes.md",
    "title": "rag_notes.md",
    "section": "Retrieval",
    "chunk_id": "rag_notes.md::structured::0004",
    "strategy": "structured"
  },
  "embedding": [
    0.012,
    -0.041,
    0.087
  ]
}
```

---

# Почему используется Structured Index

На Дне 21 были созданы два индекса:

```text
index_fixed.json
index_structured.json
```

Для первого RAG-запроса выбран:

```text
index_structured.json
```

Structured chunks дополнительно содержат информацию о логических разделах документа.

Например:

```text
File:
rag_notes.md

Section:
Retrieval
```

Это делает найденный контекст более понятным при выводе источников.

---

# Query Embedding

Для поиска вопрос сначала преобразуется в embedding:

```text
Question
   ↓
Embedding Model
   ↓
Vector
```

Например концептуально:

```text
"Зачем используется overlap?"

↓

[0.12, -0.04, 0.08, ...]
```

Функция:

```python
create_query_embedding()
```

создаёт embedding пользовательского вопроса.

---

# Совместимость Embeddings

Document embeddings и query embedding должны использовать совместимую конфигурацию.

Индекс Дня 21 и запрос Дня 22 используют одну embedding-модель и одинаковую размерность.

В проекте:

```text
Embedding dimensions: 768
```

Это позволяет корректно сравнивать vectors.

---

# Поиск релевантных chunks

Функция:

```python
search_chunks()
```

сравнивает embedding вопроса с embedding каждого chunk в локальном индексе.

Pipeline:

```text
Query Embedding
       ↓
┌──────┼──────────────┐
↓      ↓              ↓
Chunk1 Chunk2 ... ChunkN
↓      ↓              ↓
score  score          score
       ↓
sort descending
       ↓
TOP-K
```

---

# Cosine Similarity

Для сравнения vectors используется cosine similarity:

```text
                 A · B
cos(A, B) = ----------------
              ||A|| × ||B||
```

Где:

```text
A = embedding вопроса
B = embedding chunk
```

Чем выше similarity, тем ближе содержание chunk к пользовательскому вопросу.

---

# Почему поиск выполняется по всем chunks

Индекс учебный и относительно небольшой.

Поэтому можно выполнить:

```text
Query
  ↓
compare with chunk 1
compare with chunk 2
compare with chunk 3
...
compare with chunk N
```

После этого результаты сортируются.

Для небольшого локального корпуса этого достаточно.

Для больших баз обычно применяются специализированные vector indexes и vector databases.

---

# TOP-K

После расчёта similarity выбираются наиболее релевантные chunks.

В проекте:

```python
TOP_K = 4
```

То есть:

```text
All Chunks
    ↓
Similarity
    ↓
Sorting
    ↓
Top 4
```

Именно эти четыре chunks передаются модели как дополнительный контекст.

---

# Вывод найденных источников

Перед RAG-ответом программа показывает найденные chunks.

Например:

```text
============================================================
НАЙДЕННЫЕ CHUNKS
============================================================

1. rag_notes.md
   Section: Retrieval
   Chunk ID: rag_notes.md::structured::0004
   Similarity: ...

2. chunking_comparison.md
   Section: Purpose
   Chunk ID: ...
   Similarity: ...
```

Это позволяет отдельно проверить качество retrieval.

---

# Metadata

Для каждого найденного chunk доступны:

```text
source
title
section
chunk_id
strategy
```

Это позволяет понять:

```text
откуда пришла информация
```

ещё до генерации ответа LLM.

---

# Построение Context

Функция:

```python
build_context()
```

объединяет найденные chunks.

Каждый источник передаётся примерно в таком формате:

```text
--- SOURCE 1 ---

File:
rag_notes.md

Section:
Retrieval

Chunk ID:
rag_notes.md::structured::0004

Text:
...
```

После этого несколько источников объединяются:

```text
SOURCE 1

SOURCE 2

SOURCE 3

SOURCE 4
```

---

# RAG Prompt

После retrieval модель получает:

```text
Instructions
+
Retrieved Context
+
User Question
```

То есть:

```text
CONTEXT:

[chunk 1]

[chunk 2]

[chunk 3]

[chunk 4]


QUESTION:

вопрос пользователя
```

Модели дополнительно указывается:

```text
использовать информацию из context
```

и:

```text
не придумывать отсутствующие в документах факты
```

Если информации недостаточно, модель должна сообщить об этом.

---

# Полный RAG Flow

```text
USER QUESTION
      ↓
create_query_embedding()
      ↓
QUERY VECTOR
      ↓
search_chunks()
      ↓
COSINE SIMILARITY
      ↓
SORT
      ↓
TOP-4 CHUNKS
      ↓
build_context()
      ↓
CONTEXT + QUESTION
      ↓
ask_with_rag()
      ↓
GEMINI
      ↓
RAG ANSWER
```

---

# Сравнение WITH RAG / WITHOUT RAG

Один вопрос проходит через два независимых режима.

```text
                     ┌───────────────────┐
                     │     QUESTION      │
                     └─────────┬─────────┘
                               │
                  ┌────────────┴────────────┐
                  ↓                         ↓
            WITHOUT RAG                 WITH RAG
                  ↓                         ↓
                Gemini               Query Embedding
                  ↓                         ↓
               Answer                 Local Index
                                            ↓
                                       Retrieval
                                            ↓
                                        Top-K
                                            ↓
                                     Context + Question
                                            ↓
                                          Gemini
                                            ↓
                                         Answer
```

Это позволяет сравнить обычный ответ модели с ответом, основанным на локальной базе документов.

---

# Почему RAG не означает автоматически лучший ответ

Обычная модель уже может хорошо отвечать на общеизвестные вопросы.

Например:

```text
Что такое embeddings?
```

может получить хороший ответ и без RAG.

Основная ценность RAG проявляется, когда вопрос относится к конкретной локальной базе:

```text
Какие metadata сохраняются
для каждого chunk в нашем проекте?
```

Без RAG модель знает общую концепцию metadata.

Но она не обязана знать конкретную структуру нашего проекта.

RAG позволяет найти именно локальные данные:

```text
source
title
section
chunk_id
strategy
```

---

# Контрольный набор

Для проверки создан файл:

```text
control_questions.json
```

Он содержит 10 контрольных вопросов.

Каждый тест содержит:

```text
question
expected
expected_sources
```

---

# Структура контрольного теста

Например:

```json
{
  "id": 1,
  "question": "Какие metadata сохраняются для каждого chunk?",
  "expected": "В ответе должны быть source, title, section, chunk_id и strategy.",
  "expected_sources": [
    "README.md",
    "chunking_comparison.md"
  ]
}
```

Таким образом для каждого вопроса заранее известно:

```text
что ожидается в ответе
```

и:

```text
какие документы желательно найти
```

---

# 10 контрольных вопросов

Контрольный набор проверяет несколько областей локальной базы.

## 1. Chunk Metadata

```text
Какие metadata сохраняются для каждого chunk?
```

Ожидается:

```text
source
title
section
chunk_id
strategy
```

Источники:

```text
README.md
chunking_comparison.md
```

---

## 2. Fixed Chunking

```text
В чем недостаток fixed-size chunking?
```

Ожидается объяснение того, что фиксированная граница может разрывать логические единицы текста.

Источники:

```text
README.md
chunking_comparison.md
```

---

## 3. Chunk Overlap

```text
Зачем используется overlap между chunks?
```

Ожидается объяснение сохранения контекста на границах.

Источники:

```text
rag_notes.md
chunking_comparison.md
```

---

## 4. RAG Ingestion

```text
Что происходит на этапе ingestion в RAG?
```

Ожидается:

```text
loading
normalization
chunking
embeddings
indexing
```

Источник:

```text
rag_notes.md
```

---

## 5. MCP Orchestration

```text
Какую роль выполняет orchestrator
при работе с несколькими MCP-серверами?
```

Источники:

```text
mcp_notes.md
agent_design.txt
```

---

## 6. Agent Memory

```text
Чем working memory отличается
от long-term memory агента?
```

Источник:

```text
agent_design.txt
```

---

## 7. Android MVVM

```text
Какую роль ViewModel выполняет в MVVM?
```

Источник:

```text
android_architecture.md
```

---

## 8. JSON Index

```text
Почему JSON удобен
для учебного локального индекса?
```

Источники:

```text
README.md
software_architecture.md
```

---

## 9. Structured Chunk Size

```text
Почему structured chunking
всё равно должен ограничивать
максимальный размер chunk?
```

Источник:

```text
chunking_comparison.md
```

---

## 10. RAG Failure Modes

```text
Какие проблемы могут ухудшить качество RAG?
```

Источник:

```text
rag_notes.md
```

---

# Зачем нужен контрольный набор

Без заранее подготовленных вопросов легко оценивать систему субъективно:

```text
"Ответ выглядит нормально"
```

Контрольный набор добавляет критерии:

```text
Question
    ↓
Expected Content
    ↓
Expected Sources
```

Теперь можно отдельно проверять:

```text
Retrieval Quality
```

и:

```text
Answer Quality
```

---

# Retrieval Quality

Если вопрос:

```text
Зачем используется overlap между chunks?
```

ожидаемые документы:

```text
rag_notes.md
chunking_comparison.md
```

Если retrieval действительно возвращает эти документы среди наиболее релевантных chunks, поиск работает ожидаемо.

Если вместо них появляются только нерелевантные документы, проблема находится на retrieval-этапе.

---

# Answer Quality

Даже при хорошем retrieval модель ещё должна правильно использовать полученный context.

Поэтому RAG состоит из двух разных задач:

```text
1. Найти правильную информацию.

2. Сформировать правильный ответ
   на основе этой информации.
```

Хороший RAG требует работы обоих этапов.

---

# Запуск

Если индекс уже существует:

```powershell
py main.py
```

Если индекс отсутствует:

```powershell
py index_documents.py
```

а затем:

```powershell
py main.py
```

---

# Первый тест

Например:

```text
Какие metadata сохраняются для каждого chunk?
```

Программа сначала показывает:

```text
БЕЗ RAG
```

затем:

```text
НАЙДЕННЫЕ CHUNKS
```

и после этого:

```text
С RAG
```

---

# Второй тест

```text
Почему structured chunking всё равно должен
ограничивать максимальный размер chunk?
```

Ожидаемый источник:

```text
chunking_comparison.md
```

---

# Третий тест

```text
Какую роль выполняет orchestrator
при работе с несколькими MCP-серверами?
```

Ожидаемые источники:

```text
mcp_notes.md
agent_design.txt
```

---

# Что показать на видео

Удобный демонстрационный вопрос:

```text
Какие metadata сохраняются для каждого chunk?
```

На одном экране можно показать:

```text
1. Question

2. WITHOUT RAG answer

3. Retrieved Top-K chunks

4. File / Section / Chunk ID / Similarity

5. WITH RAG answer
```

После этого открыть:

```text
control_questions.json
```

и показать:

```text
question
expected
expected_sources
```

---

# Результат

Реализован первый локальный RAG pipeline:

```text
Question
    ↓
Embedding
    ↓
Vector Search
    ↓
Top-K Chunks
    ↓
Context
    ↓
LLM
    ↓
Answer
```

Также реализован baseline:

```text
Question
    ↓
LLM
    ↓
Answer Without RAG
```

Благодаря этому ответы можно сравнивать.

---

# Реализовано

- загрузка локального vector index;
- embedding пользовательского вопроса;
- cosine similarity;
- поиск по всем chunks;
- сортировка по similarity;
- Top-K retrieval;
- вывод найденных источников;
- metadata источников;
- построение RAG context;
- запрос к LLM без RAG;
- запрос к LLM с RAG;
- сравнение двух режимов;
- 10 контрольных вопросов;
- ожидаемое содержание ответов;
- ожидаемые источники.

---

# Итоговая архитектура

```text
                        USER
                          ↓
                       QUESTION
                          ↓
            ┌─────────────┴─────────────┐
            │                           │
            ↓                           ↓
       WITHOUT RAG                   WITH RAG
            │                           │
            ↓                           ↓
           LLM                    Query Embedding
            │                           │
            │                           ↓
            │                      Local Index
            │                           │
            │                           ↓
            │                   Cosine Similarity
            │                           │
            │                           ↓
            │                        Top-K
            │                           │
            │                           ↓
            │                    Retrieved Context
            │                           │
            │                           ↓
            │                          LLM
            │                           │
            ↓                           ↓
         ANSWER                      ANSWER
            │                           │
            └─────────────┬─────────────┘
                          ↓
                       COMPARE
```

---

# Вывод

На Дне 21 была создана база для retrieval:

```text
Documents
→ Chunks
→ Embeddings
→ Index
```

На Дне 22 индекс впервые начал использоваться:

```text
Question
→ Query Embedding
→ Similarity Search
→ Relevant Chunks
→ Context
→ LLM
```

Таким образом был реализован первый полный RAG-запрос и создан baseline для сравнения ответов модели с использованием локальной базы документов и без неё.