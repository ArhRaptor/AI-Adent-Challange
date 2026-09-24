import time
from datetime import datetime

from storage import (
    load_tasks,
    save_tasks,
    add_monitoring_record
)

from warehouse_api import (
    get_product
)


# ============================================================
# CHECK TASK
# ============================================================

def should_run(task):

    if not task.get(
        "enabled",
        True
    ):
        return False

    last_run = task.get(
        "last_run"
    )

    if last_run is None:
        return True

    last_time = (
        datetime.fromisoformat(
            last_run
        )
    )

    now = datetime.now()

    elapsed = (
        now - last_time
    ).total_seconds()

    return (
        elapsed
        >= task["interval_seconds"]
    )


# ============================================================
# EXECUTE
# ============================================================

def execute_task(task):

    product_id = (
        task["product_id"]
    )

    print()
    print("-" * 60)

    print(
        f"Выполняем задачу "
        f"{task['id']}"
    )

    print(
        f"Product ID: "
        f"{product_id}"
    )

    product = get_product(
        product_id
    )

    if product is None:

        print(
            "Товар не найден."
        )

        return

    add_monitoring_record(
        task["id"],
        product
    )

    task["last_run"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    print(
        f"Количество: "
        f"{product['quantity']}"
    )

    print(
        "Данные сохранены."
    )


# ============================================================
# WORKER
# ============================================================

def main():

    print("=" * 60)
    print(
        "ДЕНЬ 18 — BACKGROUND WORKER"
    )
    print("=" * 60)

    print()
    print(
        "Worker запущен."
    )

    print(
        "Для остановки нажмите Ctrl+C."
    )

    try:

        while True:

            tasks = load_tasks()

            changed = False

            for task in tasks:

                if should_run(task):

                    execute_task(task)

                    changed = True

            if changed:

                save_tasks(tasks)

            # Worker проверяет расписание
            # каждую секунду.

            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print()
        print(
            "Worker остановлен."
        )


if __name__ == "__main__":
    main()