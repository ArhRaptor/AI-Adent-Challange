# День 18 — Планировщик и фоновые задачи

## Цель

Добавить в MCP-агента поддержку отложенных и периодических фоновых задач.

Агент должен уметь:

- создавать периодическую задачу через MCP;
- сохранять расписание;
- выполнять задачу в фоне;
- сохранять результаты выполнения;
- накапливать данные;
- агрегировать накопленные результаты;
- передавать итоговую сводку AI-агенту.

В качестве примера реализован периодический мониторинг остатков товаров на складе.

---

# Архитектура

На предыдущем этапе агент мог вызвать MCP-инструмент один раз:

```text
USER
 ↓
MCP Client
 ↓
MCP Server
 ↓
Tool
 ↓
Result
 ↓
Gemini
```

На Дне 18 добавляется отдельный фоновый процесс:

```text
                  ┌───────────────────┐
                  │     worker.py     │
                  │ background worker │
                  └─────────┬─────────┘
                            │
                      каждые N секунд
                            ↓
                  scheduled_tasks.json
                            │
                            ↓
                     Warehouse API
                            │
                            ↓
                  monitoring_data.json


USER
 ↓
main.py
 ↓
MCP Client
 ↓
MCP Server
 ↓
get_summary()
 ↓
Aggregated Result
 ↓
Gemini
 ↓
Summary
```

Таким образом выполнение задачи больше не зависит от одного запроса пользователя.

---

# Структура проекта

```text
.
├── main.py
├── mcp_server.py
├── worker.py
├── storage.py
├── warehouse_api.py
├── README.md
├── scheduled_tasks.json
└── monitoring_data.json
```

Основные роли файлов:

```text
main.py
→ MCP Client + Gemini Agent

mcp_server.py
→ MCP Server + управление задачами

worker.py
→ фоновое периодическое выполнение

storage.py
→ работа с JSON

warehouse_api.py
→ Mock API склада

scheduled_tasks.json
→ сохранённые задачи

monitoring_data.json
→ результаты фонового мониторинга
```

---

# MCP-инструменты

MCP Server предоставляет три инструмента:

```text
create_monitoring_task
list_tasks
get_summary
```

Каждый отвечает за отдельную часть работы планировщика.

---

# create_monitoring_task

Инструмент создаёт новую периодическую задачу.

Входные параметры:

```text
product_id
interval_seconds
```

Пример:

```text
product_id = 101
interval_seconds = 10
```

означает:

```text
Проверять товар 101 каждые 10 секунд.
```

Инструмент создаёт задачу:

```json
{
  "id": "...",
  "product_id": 101,
  "interval_seconds": 10,
  "enabled": true,
  "last_run": null
}
```

и сохраняет её в:

```text
scheduled_tasks.json
```

---

# Persistence

Одна из основных частей задания — сохранение данных.

В проекте используются два JSON-хранилища.

## scheduled_tasks.json

Содержит расписание:

```json
[
  {
    "id": "...",
    "product_id": 101,
    "interval_seconds": 10,
    "enabled": true,
    "last_run": null
  }
]
```

Задача не существует только в оперативной памяти Python.

После завершения MCP-клиента информация остаётся на диске.

---

## monitoring_data.json

Содержит результаты фоновых запусков.

Например:

```json
[
  {
    "task_id": "...",
    "timestamp": "2026-09-24T17:30:00",
    "product": {
      "id": 101,
      "name": "Ноутбук Lenovo ThinkBook",
      "quantity": 7,
      "price": 85000,
      "warehouse": "Москва"
    }
  }
]
```

При каждом выполнении задачи добавляется новая запись.

Получается история:

```text
RUN #1
  ↓
measurement

RUN #2
  ↓
measurement

RUN #3
  ↓
measurement

...

monitoring_data.json
```

---

# storage.py

Работа с файлами вынесена в отдельный модуль:

```text
storage.py
```

Он отвечает за:

```text
load_json()
save_json()

load_tasks()
save_tasks()

load_monitoring_data()
save_monitoring_data()

add_monitoring_record()
```

Таким образом бизнес-логика не смешивается с кодом хранения данных.

---

# Warehouse API

Источник данных вынесен в:

```text
warehouse_api.py
```

Для учебного проекта используется Mock API:

```python
PRODUCTS = {
    101: {...},
    102: {...},
    103: {...}
}
```

Получение товара:

```python
get_product(product_id)
```

В production-проекте вместо Mock API здесь может находиться:

```text
REST API
Database
CRM
ERP
Яндекс.Трекер
другая внешняя система
```

Архитектура MCP и фонового worker при этом может остаться прежней.

---

# Background Worker

Главная новая часть Дня 18:

```text
worker.py
```

Worker запускается отдельно от MCP-клиента.

Основной принцип:

```python
while True:
    ...
```

Процесс постоянно работает и проверяет сохранённые задачи.

Схема:

```text
worker.py
    ↓
load_tasks()
    ↓
для каждой задачи
    ↓
should_run()
   /     \
 NO      YES
          ↓
    execute_task()
          ↓
    Warehouse API
          ↓
    сохранить результат
```

---

# Проверка расписания

Для каждой задачи worker проверяет:

```text
enabled
last_run
interval_seconds
```

Если задача ещё никогда не запускалась:

```text
last_run = null
```

она может быть выполнена сразу.

Если задача уже запускалась, рассчитывается:

```text
now - last_run
```

Если прошло не меньше:

```text
interval_seconds
```

задача запускается снова.

---

# Выполнение задачи

При наступлении времени выполнения worker вызывает:

```python
get_product(product_id)
```

После получения данных создаётся запись мониторинга:

```text
task_id
timestamp
product
```

и сохраняется в:

```text
monitoring_data.json
```

После выполнения обновляется:

```text
last_run
```

в расписании.

---

# Почему Worker отделён от MCP Server

MCP Server отвечает за команды:

```text
создать задачу
показать задачи
получить сводку
```

Worker отвечает за:

```text
периодически выполнять задачи
```

Это намеренное разделение:

```text
MCP SERVER
→ управление

WORKER
→ выполнение
```

Если бы бесконечный цикл планировщика находился внутри обычного MCP-клиента, фоновые задачи прекратились бы вместе с клиентским процессом.

---

# Запуск фонового Worker

Worker запускается в отдельном PowerShell:

```powershell
py worker.py
```

После запуска:

```text
Worker запущен.
Для остановки нажмите Ctrl+C.
```

Worker продолжает проверять расписание до остановки процесса.

---

# Создание задачи

В другом окне PowerShell запускается:

```powershell
py main.py
```

Выбирается:

```text
1 — Создать мониторинг
```

Например:

```text
ID товара: 101
Интервал в секундах: 10
```

MCP Client вызывает:

```text
create_monitoring_task
```

MCP Server сохраняет задачу в:

```text
scheduled_tasks.json
```

После этого worker может обнаружить её самостоятельно.

---

# Периодическое выполнение

Для учебной демонстрации можно использовать небольшой интервал:

```text
10 секунд
```

Тогда процесс выглядит примерно так:

```text
00:00
↓
RUN #1

00:10
↓
RUN #2

00:20
↓
RUN #3

00:30
↓
RUN #4
```

Каждый запуск создаёт новую запись в:

```text
monitoring_data.json
```

В production вместо секунд обычно использовались бы более реальные интервалы:

```text
5 минут
1 час
1 день
```

---

# list_tasks

Второй MCP-инструмент:

```text
list_tasks
```

возвращает сохранённые фоновые задачи.

Например:

```json
{
  "success": true,
  "count": 1,
  "tasks": [
    {
      "id": "...",
      "product_id": 101,
      "interval_seconds": 10,
      "enabled": true,
      "last_run": "..."
    }
  ]
}
```

Это позволяет через MCP проверить текущее расписание.

---

# Агрегация данных

Третий MCP-инструмент:

```text
get_summary
```

получает:

```text
product_id
```

и анализирует все накопленные измерения этого товара.

Вычисляются:

```text
measurements
current_quantity
min_quantity
max_quantity
average_quantity
last_measurement
```

Таким образом MCP Tool возвращает уже не отдельное измерение, а агрегированный результат.

---

# Пример агрегированного результата

После нескольких запусков структура может выглядеть так:

```json
{
  "success": true,
  "product_id": 101,
  "product_name": "Ноутбук Lenovo ThinkBook",
  "measurements": 3,
  "current_quantity": 7,
  "min_quantity": 7,
  "max_quantity": 7,
  "average_quantity": 7.0,
  "last_measurement": "..."
}
```

---

# Почему min/max пока одинаковые

Mock API содержит статические данные.

Например:

```text
quantity = 7
```

Поэтому последовательность измерений может быть:

```text
7
7
7
7
```

Тогда:

```text
current = 7
min = 7
max = 7
average = 7
```

Это нормальное поведение.

При использовании реального API остаток мог бы меняться:

```text
7
5
9
4
```

Тогда:

```text
current = 4
min = 4
max = 9
average = 6.25
```

---

# Использование результата агентом

После вызова:

```text
get_summary
```

MCP Client получает агрегированные данные.

Затем они передаются Gemini:

```text
MCP SUMMARY
     ↓
Gemini Agent
     ↓
AGENT SUMMARY
```

Gemini получает инструкции использовать только данные MCP и сформировать понятную сводку.

Например агент может сообщить:

```text
Товар: Ноутбук Lenovo ThinkBook

Количество измерений: 3
Текущий остаток: 7
Минимальный остаток: 7
Максимальный остаток: 7
Средний остаток: 7
Последнее измерение: ...
```

Точная формулировка ответа зависит от модели.

---

# Полный жизненный цикл

Полный сценарий выглядит так:

```text
USER
 │
 │ создать мониторинг
 ↓
main.py
 ↓
MCP Client
 ↓
create_monitoring_task
 ↓
MCP Server
 ↓
scheduled_tasks.json
        │
        │
        ↓
    worker.py
        │
        │ каждые N секунд
        ↓
  Warehouse API
        ↓
monitoring_data.json
        │
        │ накапливает данные
        ↓
    get_summary
        ↓
 Aggregated Result
        ↓
      Gemini
        ↓
   Human Summary
```

---

# Проверка

## 1. Очистить тестовые данные

При необходимости:

```powershell
Remove-Item scheduled_tasks.json -ErrorAction SilentlyContinue
Remove-Item monitoring_data.json -ErrorAction SilentlyContinue
```

## 2. Создать задачу

```powershell
py main.py
```

Выбрать:

```text
1
```

Затем:

```text
ID товара: 101
Интервал в секундах: 10
```

## 3. Запустить Worker

Во втором PowerShell:

```powershell
py worker.py
```

## 4. Подождать несколько запусков

Например 20–30 секунд.

Worker должен несколько раз выполнить задачу и сохранить результаты.

## 5. Получить сводку

Снова:

```powershell
py main.py
```

Выбрать:

```text
3
```

И:

```text
ID товара: 101
```

MCP возвращает агрегированный результат, после чего Gemini формирует читаемую сводку.

---

# Работа 24/7

В учебной реализации `worker.py` представляет собой постоянно работающий процесс:

```text
worker.py
   ↓
while True
   ↓
check schedule
   ↓
execute
   ↓
sleep
   ↓
repeat
```

Пока процесс запущен, задачи продолжают выполняться независимо от MCP-клиента.

Важно: это не означает, что программа продолжит работать после выключения компьютера.

Для настоящего режима 24/7 worker необходимо разместить в постоянно работающей среде, например:

```text
Windows Service
Linux Service
Docker
Cloud VM
Server
```

Также production-система обычно добавляет автоматический перезапуск процесса, логирование и обработку сбоев.

---

# День 17 vs День 18

## День 17

Инструмент выполнялся непосредственно по запросу:

```text
USER
 ↓
call_tool()
 ↓
RESULT
```

## День 18

Теперь пользователь может создать задачу:

```text
USER
 ↓
CREATE TASK
 ↓
SAVE
```

после чего worker выполняет её самостоятельно:

```text
WORKER
 ↓
SCHEDULE
 ↓
RUN
 ↓
SAVE RESULT
 ↓
RUN AGAIN
 ↓
SAVE RESULT
```

А позже агент получает агрегированную информацию:

```text
HISTORY
 ↓
AGGREGATION
 ↓
MCP
 ↓
GEMINI
 ↓
SUMMARY
```

---

# Результат

В результате реализован MCP-агент с фоновыми периодическими задачами.

Система умеет:

- создавать периодические задачи через MCP;
- задавать интервал выполнения;
- сохранять задачи в JSON;
- восстанавливать расписание из JSON;
- запускать отдельный background worker;
- выполнять задачи по расписанию;
- обращаться к Mock API;
- сохранять результаты каждого запуска;
- накапливать историю измерений;
- получать список задач;
- агрегировать накопленные данные;
- рассчитывать min/max/average/current;
- возвращать результат через MCP;
- передавать агрегированную информацию Gemini;
- формировать понятную пользователю сводку.

---

# Вывод

На предыдущем этапе MCP отвечал на запрос непосредственно:

```text
REQUEST
 ↓
TOOL
 ↓
RESULT
```

Теперь появляется долговременный процесс:

```text
REQUEST
 ↓
SCHEDULE
 ↓
PERSIST
 ↓
BACKGROUND WORKER
 ↓
PERIODIC EXECUTION
 ↓
DATA COLLECTION
 ↓
AGGREGATION
 ↓
MCP
 ↓
GEMINI
 ↓
SUMMARY
```

Это позволяет перейти от обычного агента, реагирующего только на сообщения пользователя, к системе, которая может самостоятельно выполнять работу между пользовательскими запросами.