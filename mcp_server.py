from mcp.server import MCPServer

import uuid

from storage import (
    load_tasks,
    save_tasks,
    load_monitoring_data
)


mcp = MCPServer(
    "Warehouse Scheduler MCP",
    instructions=(
        "MCP-сервер для фонового "
        "мониторинга склада."
    )
)


# ============================================================
# CREATE TASK
# ============================================================

@mcp.tool(
    title="Создать мониторинг товара",
    description=(
        "Создаёт периодическую задачу "
        "для мониторинга товара."
    )
)
def create_monitoring_task(
    product_id: int,
    interval_seconds: int
) -> dict:

    if interval_seconds < 5:

        return {
            "success": False,
            "error": (
                "Минимальный интервал "
                "для учебного примера — "
                "5 секунд."
            )
        }

    tasks = load_tasks()

    task = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "interval_seconds":
            interval_seconds,
        "enabled": True,
        "last_run": None
    }

    tasks.append(task)

    save_tasks(tasks)

    return {
        "success": True,
        "task": task
    }


# ============================================================
# LIST TASKS
# ============================================================

@mcp.tool(
    title="Список фоновых задач",
    description=(
        "Возвращает список "
        "запланированных задач."
    )
)
def list_tasks() -> dict:

    tasks = load_tasks()

    return {
        "success": True,
        "count": len(tasks),
        "tasks": tasks
    }


# ============================================================
# SUMMARY
# ============================================================

@mcp.tool(
    title="Сводка мониторинга",
    description=(
        "Возвращает агрегированную "
        "сводку собранных данных "
        "по товару."
    )
)
def get_summary(
    product_id: int
) -> dict:

    data = load_monitoring_data()

    records = [
        record
        for record in data
        if record["product"]["id"]
        == product_id
    ]

    if not records:

        return {
            "success": False,
            "error": (
                "Данных мониторинга "
                "пока нет."
            ),
            "product_id": product_id
        }

    quantities = [
        record["product"]["quantity"]
        for record in records
    ]

    latest = records[-1]

    return {
        "success": True,

        "product_id":
            product_id,

        "product_name":
            latest["product"]["name"],

        "measurements":
            len(records),

        "current_quantity":
            quantities[-1],

        "min_quantity":
            min(quantities),

        "max_quantity":
            max(quantities),

        "average_quantity":
            sum(quantities)
            / len(quantities),

        "last_measurement":
            latest["timestamp"]
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    mcp.run()