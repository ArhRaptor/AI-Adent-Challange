import json
import os
from datetime import datetime


TASKS_FILE = "scheduled_tasks.json"
DATA_FILE = "monitoring_data.json"


# ============================================================
# JSON
# ============================================================

def load_json(
    filename,
    default
):
    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
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
    filename,
    data
):

    with open(
        filename,
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
# TASKS
# ============================================================

def load_tasks():

    return load_json(
        TASKS_FILE,
        []
    )


def save_tasks(tasks):

    save_json(
        TASKS_FILE,
        tasks
    )


# ============================================================
# MONITORING DATA
# ============================================================

def load_monitoring_data():

    return load_json(
        DATA_FILE,
        []
    )


def save_monitoring_data(data):

    save_json(
        DATA_FILE,
        data
    )


def add_monitoring_record(
    task_id,
    product
):

    data = load_monitoring_data()

    record = {
        "task_id": task_id,
        "timestamp": (
            datetime.now().isoformat(
                timespec="seconds"
            )
        ),
        "product": product
    }

    data.append(record)

    save_monitoring_data(data)