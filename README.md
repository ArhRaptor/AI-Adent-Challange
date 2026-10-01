# День 24 — Цитаты, источники и анти-галлюцинации

## Цель

Доработать RAG-систему так, чтобы каждый содержательный ответ был проверяемым.

Теперь система должна возвращать:

```text
Answer
+
Sources
+
Quotes
```

При этом источники и цитаты не просто запрашиваются у LLM — они дополнительно проверяются программно.

Также добавлен режим отказа от ответа:

```text
низкая релевантность
        ↓
"Не знаю"
        ↓
просьба уточнить вопрос
```

Главная задача Дня 24:

```text
не просто получить ответ,
а показать, на каких данных
этот ответ основан
```

---

# Развитие RAG

## День 21 — Indexing

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

## День 22 — First RAG

```text
Question
    ↓
Embedding
    ↓
Retrieval
    ↓
Top-K
    ↓
Context
    ↓
LLM
```

## День 23 — Improved Retrieval

```text
Question
    ↓
Query Rewrite
    ↓
Top-K Candidates
    ↓
Similarity Filter
    ↓
Relevant Chunks
    ↓
LLM
```

## День 24 — Grounded RAG

```text
Question
    ↓
Query Rewrite
    ↓
Retrieval
    ↓
Similarity Filter
    ↓
Relevance Gate
    ↓
Grounded Generation
    ↓
Sources + Quotes
    ↓
Validation
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

# Полная архитектура Day 24

```text
                         USER
                           ↓
                        QUESTION
                           ↓
                     Query Rewrite
                           ↓
                     Query Embedding
                           ↓
                      Local Index
                           ↓
                    Vector Retrieval
                           ↓
                    Top-8 Candidates
                           ↓
                   Similarity Filter
                           ↓
                      Top-4 max
                           ↓
                    Relevance Gate
                           │
                 ┌─────────┴─────────┐
                 ↓                   ↓
             relevant            insufficient
                 ↓                   ↓
         Build Context          "Не знаю"
                 ↓                   ↓
                LLM          Ask for clarification
                 ↓
         Structured JSON
                 ↓
      ┌──────────┼──────────┐
      ↓          ↓          ↓
    Answer    Sources     Quotes
      └──────────┼──────────┘
                 ↓
             Validation
```

---

# Настройки Retrieval

В проекте используются:

```python
TOP_K_BEFORE_FILTER = 8
TOP_K_AFTER_FILTER = 4

SIMILARITY_THRESHOLD = 0.45
```

Сначала система получает до восьми кандидатов:

```text
Vector Search
     ↓
Top-8
```

После этого применяется threshold:

```text
score >= 0.45
```

И только после фильтра выбирается максимум:

```text
Top-4
```

---

# Query Rewrite

Пользовательский вопрос сначала преобразуется в более подходящую формулировку для semantic search.

Функция:

```python
rewrite_query()
```

Pipeline:

```text
Original Question
       ↓
      LLM
       ↓
Rewritten Search Query
```

Rewrite используется только для поиска.

Для генерации финального ответа сохраняется оригинальный вопрос пользователя.

```text
Original Question
      │
      ├──────────────→ Final Answer
      │
      ↓
Query Rewrite
      ↓
Retrieval
```

---

# Retrieval

После rewriting создаётся query embedding.

```text
Query
  ↓
Embedding
  ↓
Vector
```

Затем embedding вопроса сравнивается с embeddings chunks локального индекса.

Используется cosine similarity:

```text
                 A · B
cos(A, B) = ----------------
              ||A|| × ||B||
```

Где:

```text
A = query embedding
B = chunk embedding
```

---

# Similarity Filtering

Простой Top-K всегда способен вернуть несколько результатов.

Но:

```text
best available result
```

не обязательно означает:

```text
relevant result
```

Поэтому после retrieval применяется:

```python
filter_chunks()
```

Chunk остаётся только если:

```text
similarity >= threshold
```

---

# Relevance Gate

После filtering выполняется дополнительная проверка:

```python
should_abstain()
```

Она решает:

```text
можно ли вообще отвечать
```

Архитектура:

```text
Filtered Chunks
       ↓
Relevance Gate
       │
   ┌───┴───┐
   ↓       ↓
 strong   weak
   ↓       ↓
  LLM   "Не знаю"
```

---

# Почему Relevance Gate находится до LLM

Можно было написать в prompt:

```text
Если данных мало — скажи "не знаю".
```

Но это оставляет решение за генеративной моделью.

В проекте используется более строгий подход:

```text
Python проверяет relevance
        ↓
если context слабый
        ↓
LLM вообще не вызывается
```

Это уменьшает вероятность того, что модель попытается ответить на основе собственных знаний при отсутствии данных в локальной базе.

---

# Режим «Не знаю»

Если подходящего контекста нет, система возвращает:

```text
Не знаю. В локальной базе недостаточно
релевантной информации.
Пожалуйста, уточните вопрос.
```

Структурно:

```json
{
  "status": "unknown",
  "answer": "Не знаю...",
  "sources": [],
  "quotes": []
}
```

Пустые `sources` и `quotes` здесь являются ожидаемым поведением.

Система сознательно не формирует содержательный ответ, который потребовал бы доказательств.

---

# Grounded Generation

Если context достаточно релевантен, найденные chunks передаются LLM.

Prompt требует использовать:

```text
ТОЛЬКО CONTEXT
```

и запрещает добавлять факты, которых нет в retrieved chunks.

Модель должна вернуть структурированный результат.

---

# Формат ответа

LLM возвращает JSON:

```json
{
  "status": "answered",
  "answer": "...",
  "sources": [
    {
      "source": "...",
      "section": "...",
      "chunk_id": "..."
    }
  ],
  "quotes": [
    {
      "chunk_id": "...",
      "quote": "..."
    }
  ]
}
```

Таким образом ответ состоит из трёх основных частей:

```text
ANSWER
+
SOURCES
+
QUOTES
```

---

# Answer

Поле:

```json
"answer"
```

содержит ответ на исходный вопрос пользователя.

Ответ должен основываться только на retrieved context.

---

# Sources

Каждый источник содержит:

```text
source
section
chunk_id
```

Пример:

```json
{
  "source": "documents/rag_notes.md",
  "section": "Retrieval",
  "chunk_id": "rag_notes.md::structured::0004"
}
```

Это позволяет определить точное происхождение информации.

---

# Почему одного имени файла недостаточно

Источник вида:

```text
rag_notes.md
```

может содержать много разных разделов.

Поэтому используется более точная ссылка:

```text
source
+
section
+
chunk_id
```

Например:

```text
documents/rag_notes.md

Section:
Retrieval

Chunk:
rag_notes.md::structured::0004
```

---

# Quotes

Кроме источника модель обязана вернуть короткие цитаты.

Формат:

```json
{
  "chunk_id": "rag_notes.md::structured::0004",
  "quote": "..."
}
```

Цитата должна быть взята непосредственно из retrieved chunk.

---

# Зачем нужны цитаты

Источник показывает:

```text
где искать доказательство
```

Цитата показывает:

```text
какой конкретно текст
используется как доказательство
```

Получается:

```text
Answer
   ↓
Claim
   ↓
Quote
   ↓
Chunk ID
   ↓
Source Document
```

---

# Anti-Hallucination Validation

Одной инструкции в prompt недостаточно.

LLM теоретически может:

```text
придумать source
придумать chunk_id
изменить quote
создать quote, которой нет в документе
```

Поэтому после генерации запускается:

```python
validate_answer()
```

---

# Проверка наличия ответа

Проверяется:

```python
result.get("answer")
```

Если answer отсутствует:

```text
Validation Error
```

---

# Проверка Sources

Сначала создаётся карта реально retrieved chunks:

```python
chunk_map = {
    chunk_id: chunk
}
```

После этого каждый source из ответа проверяется.

Если модель указала:

```text
rag_notes.md::structured::9999
```

а такого retrieved chunk нет:

```text
Validation Error
```

---

# Проверка Source Metadata

Даже существующий `chunk_id` недостаточен.

Дополнительно сравниваются:

```text
source
section
```

с реальными metadata chunk.

Таким образом модель не может корректно пройти validation, просто указав существующий ID с выдуманными metadata.

---

# Проверка Quotes

Самая строгая проверка выполняется для цитат.

Для каждой цитаты:

```python
if quote not in original_text:
```

Если строка отсутствует в исходном retrieved chunk:

```text
Validation Error
```

То есть цитата должна существовать в документе дословно.

---

# Пример

LLM возвращает:

```json
{
  "chunk_id": "rag_notes.md::structured::0004",
  "quote": "Chunk overlap preserves context."
}
```

Python получает настоящий текст:

```text
chunk["text"]
```

и проверяет:

```text
"Chunk overlap preserves context."
        IN
original chunk text
```

Если строки нет, цитата считается неподтверждённой.

---

# Validation Result

В консоли выводится:

```text
Sources present: ...
Quotes present: ...
Validation passed: ...
```

Если обнаружены ошибки, они выводятся отдельно.

Например:

```text
Validation passed: False

- Неизвестный source chunk_id: ...
- Цитата не найдена дословно в chunk: ...
```

---

# Что Validation действительно гарантирует

Программная проверка может определить:

```text
есть ли sources
есть ли quotes
существует ли chunk_id
совпадает ли source
совпадает ли section
существует ли quote дословно в chunk
```

Это детерминированные проверки.

---

# Что Validation пока не гарантирует

Текущая реализация не может строго доказать, что:

```text
весь смысл answer
логически следует из quotes
```

Например, цитата может быть настоящей, но модель может сделать из неё слишком сильный вывод.

Поэтому semantic consistency:

```text
Answer
vs
Quotes
```

проверяется отдельно на контрольных вопросах.

Это важное различие между:

```text
Citation Validation
```

и:

```text
Semantic Grounding Evaluation
```

---

# Контрольный набор

Используется:

```text
control_questions.json
```

с 10 вопросами, созданными на предыдущем этапе.

Для каждого вопроса уже определены:

```text
question
expected
expected_sources
```

На Дне 24 этот же набор используется для проверки grounded answers.

---

# Что проверяем на 10 вопросах

Для каждого содержательного ответа проверяются:

```text
1. Есть ли answer?

2. Есть ли sources?

3. Реальны ли source / section / chunk_id?

4. Есть ли quotes?

5. Существуют ли quotes дословно
   в соответствующих chunks?

6. Подтверждают ли quotes
   смысл answer?
```

Первые пять пунктов могут проверяться программно полностью или частично.

Последний требует semantic evaluation.

---

# Проверка №1 — Chunk Overlap

Вопрос:

```text
Зачем используется overlap между chunks?
```

Ожидается, что retrieval найдёт информацию о chunking.

Ответ должен содержать:

```text
Answer
Sources
Quotes
```

В конце ожидается validation report.

---

# Проверка №2 — Metadata

Вопрос:

```text
Какие metadata сохраняются
для каждого chunk?
```

Ожидаемый смысл:

```text
source
title
section
chunk_id
strategy
```

Теперь недостаточно просто перечислить эти поля.

Система должна показать документы и цитаты, которыми этот ответ подтверждается.

---

# Проверка №3 — нерелевантный вопрос

Например:

```text
Как приготовить борщ?
```

Локальная база посвящена техническим материалам и не предназначена для рецептов.

При отсутствии chunks выше откалиброванного threshold система должна перейти в:

```text
status = unknown
```

и ответить:

```text
Не знаю.
В локальной базе недостаточно
релевантной информации.
Пожалуйста, уточните вопрос.
```

При этом генерация grounded answer не выполняется.

---

# Важность Threshold Calibration

В проекте используется:

```python
SIMILARITY_THRESHOLD = 0.45
```

Это экспериментальное значение.

Оно не является универсальным threshold для любых embedding models и любых документов.

Порог следует оценивать на:

```text
релевантных вопросах
+
нерелевантных вопросах
```

Если нерелевантный вопрос проходит threshold, порог требует дополнительной настройки.

Если хорошие вопросы постоянно отбрасываются, threshold может быть слишком высоким.

---

# Три уровня защиты

Day 24 использует три разных уровня.

## Level 1 — Relevance Gate

```text
Weak Context
    ↓
STOP
    ↓
"Не знаю"
```

Не позволяет генерировать grounded answer при отсутствии достаточного контекста.

## Level 2 — Grounded Prompt

```text
Strong Context
    ↓
LLM
    ↓
Use only retrieved information
```

Ограничивает модель retrieved context.

## Level 3 — Deterministic Validation

```text
LLM Result
    ↓
Python
    ↓
Source Validation
+
Quote Validation
```

Проверяет структурированные доказательства после генерации.

---

# Полный Anti-Hallucination Pipeline

```text
Question
    ↓
Rewrite
    ↓
Retrieve
    ↓
Filter
    ↓
Relevance Gate
    │
    ├──── weak ────→ "Не знаю"
    │
    ↓ strong
Context
    ↓
Grounded Prompt
    ↓
LLM
    ↓
Answer + Sources + Quotes
    ↓
Source Validation
    ↓
Quote Validation
    ↓
Validated Result
```

---

# Запуск

Если индекс уже существует:

```powershell
py main.py
```

Если индекс необходимо создать:

```powershell
py index_documents.py
```

затем:

```powershell
py main.py
```

---

# Что показать на видео

Для демонстрации удобно использовать три сценария.

## 1. Grounded Answer

```text
Зачем используется overlap между chunks?
```

Показать:

```text
retrieval
filter
answer
sources
quotes
validation
```

## 2. Project-specific Answer

```text
Какие metadata сохраняются
для каждого chunk?
```

Показать связь:

```text
Answer
→ Quote
→ Chunk ID
→ Source
```

## 3. Abstention

```text
Как приготовить борщ?
```

При отсутствии достаточно релевантного контекста показать:

```text
filter
→ no relevant context
→ "Не знаю"
→ request clarification
→ LLM answer generation skipped
```

---

# Что реализовано

В Day 24 добавлены:

- обязательный structured answer;
- список sources;
- `source`;
- `section`;
- `chunk_id`;
- обязательные quotes;
- связь quote с chunk;
- проверка существования source;
- проверка source metadata;
- проверка существования chunk_id;
- дословная проверка quotes;
- relevance gate;
- режим `unknown`;
- ответ «Не знаю»;
- просьба уточнить вопрос;
- пропуск LLM generation при слабом context;
- validation report;
- повторное использование 10 контрольных вопросов.

---

# Результат

RAG теперь возвращает не просто текстовый ответ:

```text
Answer
```

а проверяемую структуру:

```text
Answer
   ↓
Sources
   ↓
Sections
   ↓
Chunk IDs
   ↓
Quotes
```

После этого Python проверяет, что доказательства действительно относятся к retrieved context.

---

# Итог

На предыдущих этапах RAG научился:

```text
индексировать документы
→ находить chunks
→ фильтровать chunks
```

На Дне 24 добавлен следующий уровень:

```text
найти информацию
        ↓
ответить по информации
        ↓
показать доказательства
        ↓
проверить доказательства
```

Если подходящих доказательств нет:

```text
не генерировать неподтверждённый ответ
```

а перейти в безопасный режим:

```text
"Не знаю. Пожалуйста, уточните вопрос."
```

Итоговая архитектура:

```text
Retrieve
→ Filter
→ Gate
→ Ground
→ Cite
→ Validate
```