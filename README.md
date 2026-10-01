# День 23 — Реранкинг и фильтрация RAG

## Цель

Улучшить RAG pipeline, созданный на Дне 22.

Простой Top-K retrieval всегда возвращает некоторое количество chunks, даже если пользовательский вопрос вообще не относится к локальной базе.

На Дне 23 добавлены:

```text
Query Rewrite
+
расширенный поиск кандидатов
+
Similarity Filter
+
Top-K после фильтрации
```

Теперь pipeline выглядит так:

```text
Question
    ↓
Query Rewrite
    ↓
Query Embedding
    ↓
Vector Search
    ↓
Top-K Candidates
    ↓
Similarity Filter
    ↓
Filtered Top-K
    ↓
Context
    ↓
LLM
    ↓
Answer
```

Дополнительно сохранён baseline RAG из Дня 22, чтобы сравнивать оба режима на одинаковых вопросах.

---

# Развитие проекта

## День 21

Был создан локальный индекс:

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

## День 22

Появился первый RAG:

```text
Question
    ↓
Embedding
    ↓
Similarity Search
    ↓
Top-K
    ↓
Context
    ↓
LLM
```

## День 23

Retrieval становится двухэтапным:

```text
Question
    ↓
Rewrite
    ↓
Retrieval
    ↓
Candidates
    ↓
Filter
    ↓
Relevant Chunks
    ↓
LLM
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

# Два режима RAG

Для сравнения реализованы два независимых режима.

## Mode 1 — Baseline RAG

Baseline соответствует подходу Дня 22:

```text
Original Question
        ↓
Query Embedding
        ↓
Vector Search
        ↓
Top-4
        ↓
Context
        ↓
LLM
```

Настройка:

```python
BASELINE_TOP_K = 4
```

Здесь отсутствуют:

```text
Query Rewrite
Similarity Threshold
Filtering
```

Поэтому поиск всегда возвращает четыре наиболее похожих chunk, даже если их абсолютная релевантность низкая.

---

# Mode 2 — Improved RAG

Улучшенный pipeline:

```text
Original Question
        ↓
Query Rewrite
        ↓
Rewritten Query
        ↓
Query Embedding
        ↓
Vector Search
        ↓
Top-8 Candidates
        ↓
Similarity Filter
        ↓
Maximum Top-4
        ↓
Context
        ↓
LLM
```

Основные настройки:

```python
TOP_K_BEFORE_FILTER = 8
TOP_K_AFTER_FILTER = 4

SIMILARITY_THRESHOLD = 0.45
```

`0.45` используется как экспериментальный стартовый порог и может корректироваться по реальным similarity scores конкретного индекса.

---

# Query Rewrite

Пользователь не всегда формулирует вопрос как хороший поисковый запрос.

Например:

```text
А зачем мы вообще делали этот overlap,
когда документы резали?
```

Для человека смысл понятен.

Но semantic retrieval может получить более концентрированный запрос после rewriting.

Функция:

```python
rewrite_query()
```

использует LLM для преобразования пользовательского вопроса в поисковую формулировку.

Pipeline:

```text
Natural Language Question
          ↓
         LLM
          ↓
Search-oriented Query
```

---

# Правила Query Rewrite

Модель получает ограничения:

```text
сохранить исходный смысл
не отвечать на вопрос
не добавлять новые факты
убрать разговорные слова
вернуть только поисковый запрос
```

Таким образом rewrite используется только для retrieval.

Исходный вопрос пользователя при этом сохраняется.

Именно оригинальный вопрос позже передаётся модели для формирования финального ответа.

---

# Почему это важно

Query Rewrite изменяет:

```text
что мы ищем
```

но не должен изменять:

```text
на какой вопрос отвечает пользователь
```

То есть:

```text
Original Question
      │
      ├────→ используется для final answer
      │
      ↓
Query Rewrite
      ↓
используется для retrieval
```

---

# Vector Search

После rewriting создаётся embedding поискового запроса.

```text
Rewritten Query
       ↓
Embedding Model
       ↓
Query Vector
```

Он сравнивается с embeddings chunks локального индекса.

Для сравнения используется:

```text
Cosine Similarity
```

Формула:

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

# Top-K до фильтрации

На Дне 22 сразу выбирались:

```text
Top-4
```

На Дне 23 поиск сначала выполняется шире:

```python
TOP_K_BEFORE_FILTER = 8
```

Получаем набор кандидатов:

```text
Vector Search

      ↓

Candidate 1
Candidate 2
Candidate 3
Candidate 4
Candidate 5
Candidate 6
Candidate 7
Candidate 8
```

Это ещё не означает, что все восемь результатов достаточно релевантны.

---

# Почему Top-K недостаточно

Допустим пользователь задаёт вопрос, которого вообще нет в нашей базе.

Например:

```text
Как приготовить борщ?
```

Vector search всё равно способен отсортировать документы.

Предположим:

```text
Chunk A → 0.31
Chunk B → 0.28
Chunk C → 0.24
Chunk D → 0.21
```

Это четыре лучших результата.

Но:

```text
best result
```

не обязательно означает:

```text
relevant result
```

Все результаты могут быть нерелевантными.

---

# Similarity Filter

Для решения этой проблемы добавлен второй retrieval stage.

Функция:

```python
filter_chunks()
```

оставляет только chunks:

```text
score >= SIMILARITY_THRESHOLD
```

Текущая настройка:

```python
SIMILARITY_THRESHOLD = 0.45
```

Концептуально:

```text
TOP-8

0.82  ───── PASS
0.79  ───── PASS
0.73  ───── PASS
0.69  ───── PASS
0.54  ───── PASS
0.41  ───── REMOVE
0.35  ───── REMOVE
0.29  ───── REMOVE
```

После этого применяется:

```python
TOP_K_AFTER_FILTER = 4
```

---

# Top-K после фильтрации

Таким образом используются две разные настройки.

## До фильтра

```python
TOP_K_BEFORE_FILTER = 8
```

означает:

```text
Сколько кандидатов рассмотреть?
```

## После фильтра

```python
TOP_K_AFTER_FILTER = 4
```

означает:

```text
Сколько максимум chunks
передать в LLM?
```

Pipeline:

```text
All Chunks
     ↓
Similarity Search
     ↓
Top-8 Candidates
     ↓
Threshold
     ↓
Relevant Candidates
     ↓
Top-4 Maximum
     ↓
LLM Context
```

---

# Почему не передавать все найденные chunks

Больше context не всегда означает лучше.

Нерелевантные chunks могут:

```text
увеличивать prompt
создавать шум
отвлекать модель
повышать стоимость
ухудшать grounded answer
```

Поэтому задача retrieval:

```text
не найти как можно больше текста
```

а:

```text
найти достаточно релевантного текста
```

---

# Что происходит, если ничего не найдено

Если ни один candidate не проходит threshold:

```text
Candidates
    ↓
Similarity Filter
    ↓
0 chunks
```

система не передаёт случайный context в LLM.

Вместо этого возвращается сообщение:

```text
В локальной базе не найдено
достаточно релевантной информации
для ответа.
```

Это важное отличие от простого Top-K retrieval.

---

# Baseline vs Improved

Проект позволяет сравнить оба подхода на одном вопросе.

```text
                     QUESTION
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
         BASELINE                 IMPROVED
             ↓                       ↓
      Original Query             Rewrite
             ↓                       ↓
         Embedding                Embedding
             ↓                       ↓
          Top-4                   Top-8
             │                       ↓
             │                    Filter
             │                       ↓
             │                 Top-4 Maximum
             ↓                       ↓
          Context                 Context
             ↓                       ↓
            LLM                     LLM
             ↓                       ↓
          Answer                  Answer
```

---

# Baseline Retrieval

Функция:

```python
run_baseline_rag()
```

выполняет:

```text
Original Question
        ↓
search_chunks()
        ↓
Top-4
        ↓
answer_with_context()
```

Этот режим используется как контрольная версия.

---

# Improved Retrieval

Функция:

```python
run_improved_rag()
```

выполняет:

```text
Question
    ↓
rewrite_query()
    ↓
search_chunks()
    ↓
Top-8
    ↓
filter_chunks()
    ↓
Top-4
    ↓
answer_with_context()
```

---

# Отладочный вывод

Программа специально показывает retrieval pipeline.

Сначала:

```text
QUERY REWRITE

Original:
...

Rewritten:
...
```

После этого:

```text
BEFORE FILTER (TOP-8)
```

Для каждого chunk выводятся:

```text
File
Section
Chunk ID
Similarity
```

Затем:

```text
AFTER FILTER
```

показывает только chunks, прошедшие threshold.

---

# Итоговая статистика

После выполнения программа выводит:

```text
Baseline chunks
Candidates before filter
Chunks after filter
Removed by filter
```

Например концептуально:

```text
Baseline chunks: 4
Candidates before filter: 8
Chunks after filter: 4
Removed by filter: 4
```

Конкретные значения зависят от вопроса и similarity scores.

---

# Контрольные вопросы

Сохраняется набор из 10 вопросов Дня 22:

```text
control_questions.json
```

Для каждого вопроса определены:

```text
question
expected
expected_sources
```

Это позволяет использовать одинаковый набор для сравнения разных версий retrieval.

```text
Same Questions
      ↓
Baseline Retrieval
      VS
Improved Retrieval
```

---

# Проверка релевантного вопроса

Пример:

```text
А зачем мы вообще делали overlap,
когда разбивали документы?
```

Этот тест полезен для Query Rewrite, потому что вопрос сформулирован разговорно.

Сравниваются:

```text
Baseline:
Original Query → Top-4

Improved:
Original Query
→ Rewrite
→ Top-8
→ Filter
→ Top-4
```

---

# Проверка RAG knowledge

Другой вопрос:

```text
Какие проблемы могут ухудшить качество RAG?
```

В локальной базе ожидается информация из:

```text
rag_notes.md
```

в частности из раздела о failure modes.

По результатам retrieval можно проверить:

```text
нашёл ли pipeline нужный документ
```

и:

```text
остался ли он после фильтрации
```

---

# Проверка нерелевантного вопроса

Особенно важный тест:

```text
Как приготовить борщ?
```

Локальная база посвящена:

```text
RAG
MCP
AI Agents
Android
Python
Software Architecture
Chunking
Embeddings
```

и не предназначена для рецептов.

Baseline Top-K всё равно способен вернуть несколько математически наиболее близких chunks.

Improved pipeline добавляет:

```text
Similarity Threshold
```

и может удалить кандидатов с недостаточной релевантностью.

Этот тест демонстрирует отличие:

```text
Top-K
```

от:

```text
Top-K + Relevance Filtering
```

---

# Threshold Calibration

Значение:

```python
SIMILARITY_THRESHOLD = 0.45
```

не считается универсальным порогом для любых embeddings и любых баз.

Это экспериментальная настройка проекта.

Порог необходимо оценивать по реальным данным:

```text
Relevant Questions
        ↓
Similarity Scores

Irrelevant Questions
        ↓
Similarity Scores
```

После этого можно подобрать границу, которая лучше разделяет:

```text
relevant
```

и:

```text
irrelevant
```

результаты.

---

# Почему это не отдельный Model Reranker

Задание допускает:

```text
reranker
или
relevance filter
```

В данной реализации выбран:

```text
Similarity-based Relevance Filter
```

Второй отдельной reranker-модели нет.

Поэтому архитектуру корректнее называть:

```text
RAG with Query Rewriting
and Similarity Filtering
```

Отдельный model reranker мог бы дополнительно получать:

```text
Query + Candidate Chunk
```

и вычислять новый relevance score.

Это возможное дальнейшее улучшение.

---

# Запуск

Если индекс уже создан:

```powershell
py main.py
```

Если индекса нет:

```powershell
py index_documents.py
```

затем:

```powershell
py main.py
```

---

# Что показать на видео

## Тест 1 — релевантный разговорный запрос

```text
А зачем мы вообще делали overlap,
когда разбивали документы?
```

Показать:

```text
Baseline Top-4
       ↓
Query Rewrite
       ↓
Top-8 Before Filter
       ↓
Similarity Scores
       ↓
Top-4 After Filter
       ↓
Improved Answer
```

## Тест 2 — нерелевантный запрос

```text
Как приготовить борщ?
```

Показать разницу между:

```text
Baseline Top-K
```

и:

```text
Similarity Filtering
```

---

# Что реализовано

В проект добавлены:

- Query Rewrite;
- query embedding после rewriting;
- расширенный candidate retrieval;
- Top-K до фильтрации;
- similarity threshold;
- relevance filtering;
- Top-K после фильтрации;
- обработка случая без релевантных chunks;
- baseline RAG;
- improved RAG;
- вывод similarity scores;
- сравнение двух retrieval pipelines;
- повторное использование контрольного набора из 10 вопросов.

---

# Результат

Получен улучшенный RAG pipeline:

```text
Question
    ↓
Query Rewrite
    ↓
Embedding
    ↓
Vector Search
    ↓
Top-8 Candidates
    ↓
Similarity Filter
    ↓
Top-4 Relevant Chunks
    ↓
Context
    ↓
LLM
    ↓
Answer
```

При этом сохранён baseline:

```text
Question
    ↓
Embedding
    ↓
Top-4
    ↓
LLM
```

Это позволяет экспериментально сравнивать качество retrieval и финальных ответов.

---

# Вывод

На Дне 22 система научилась находить наиболее похожие chunks.

На Дне 23 добавлена следующая важная идея:

```text
Наиболее похожий результат
не обязательно является
достаточно релевантным результатом.
```

Поэтому retrieval теперь состоит из нескольких этапов:

```text
Rewrite
    ↓
Retrieve
    ↓
Filter
    ↓
Generate
```

Так RAG получает возможность не только выбирать лучшие документы, но и отбрасывать кандидатов, которые не проходят заданный порог релевантности.