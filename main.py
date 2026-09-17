from google import genai
from google.genai import types

import json
import os
import time


# ============================================================
# TASK STATE MACHINE
# ============================================================

class TaskStateMachine:

    TRANSITIONS = {
        "planning": "execution",
        "execution": "validation",
        "validation": "done",
        "done": None
    }

    def __init__(self, filename="task_state.json"):
        self.filename = filename
        self.state = self.load()

    def default_state(self):
        return {
            "task": "",
            "stage": "planning",
            "current_step": "",
            "expected_action": "",
            "paused": False
        }

    def load(self):
        if not os.path.exists(self.filename):
            return self.default_state()

        try:
            with open(
                self.filename,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):
            return self.default_state()

    def save(self):
        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.state,
                file,
                ensure_ascii=False,
                indent=2
            )

    def start_task(self, task):
        self.state = {
            "task": task,
            "stage": "planning",
            "current_step": "Определить план выполнения задачи",
            "expected_action": "Сформировать план",
            "paused": False
        }

        self.save()

        print()
        print("Новая задача создана.")

    def set_step(
        self,
        current_step,
        expected_action
    ):
        self.state["current_step"] = current_step
        self.state["expected_action"] = expected_action

        self.save()

        print()
        print("Текущий шаг обновлён.")

    def next_stage(self):
        current = self.state["stage"]

        next_state = self.TRANSITIONS.get(
            current
        )

        if next_state is None:
            print()
            print("Задача уже завершена.")
            return

        self.state["stage"] = next_state

        if next_state == "execution":

            self.state["current_step"] = (
                "Выполнить запланированные действия"
            )

            self.state["expected_action"] = (
                "Выполнение задачи"
            )

        elif next_state == "validation":

            self.state["current_step"] = (
                "Проверить результат"
            )

            self.state["expected_action"] = (
                "Провести проверку"
            )

        elif next_state == "done":

            self.state["current_step"] = (
                "Задача завершена"
            )

            self.state["expected_action"] = (
                "Никаких действий не требуется"
            )

        self.save()

        print()
        print(
            f"Переход: {current} -> {next_state}"
        )

    def pause(self):
        self.state["paused"] = True
        self.save()

        print()
        print("Задача поставлена на паузу.")

    def resume(self):
        self.state["paused"] = False
        self.save()

        print()
        print("Задача продолжена.")

    def reset(self):
        self.state = self.default_state()
        self.save()

        print()
        print("Task State сброшен.")

    def show(self):
        print()
        print("=" * 60)
        print("TASK STATE")
        print("=" * 60)

        print(
            f"Задача:             "
            f"{self.state['task'] or 'не задана'}"
        )

        print(
            f"Этап:               "
            f"{self.state['stage']}"
        )

        print(
            f"Текущий шаг:        "
            f"{self.state['current_step'] or 'не задан'}"
        )

        print(
            f"Ожидаемое действие: "
            f"{self.state['expected_action'] or 'не задано'}"
        )

        status = (
            "PAUSED"
            if self.state["paused"]
            else "ACTIVE"
        )

        print(
            f"Статус:             {status}"
        )

    def to_prompt(self):
        return json.dumps(
            self.state,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# INVARIANTS
# ============================================================

class InvariantManager:

    def __init__(
        self,
        filename="invariants.json"
    ):
        self.filename = filename
        self.invariants = self.load()

    def load(self):
        if not os.path.exists(self.filename):
            return {}

        try:
            with open(
                self.filename,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):
            return {}

    def save(self):
        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.invariants,
                file,
                ensure_ascii=False,
                indent=2
            )

    def add(self, key, value):
        self.invariants[key] = value

        self.save()

        print()
        print("Добавлен инвариант:")
        print(f"{key} = {value}")

    def remove(self, key):
        if key not in self.invariants:
            print()
            print(
                f"Инвариант '{key}' не найден."
            )
            return

        del self.invariants[key]
        self.save()

        print()
        print(
            f"Инвариант '{key}' удалён."
        )

    def clear(self):
        self.invariants = {}
        self.save()

        print()
        print("Все инварианты удалены.")

    def show(self):
        print()
        print("=" * 60)
        print("INVARIANTS")
        print("=" * 60)

        if not self.invariants:
            print("Инвариантов нет.")
            return

        for key, value in self.invariants.items():
            print(
                f"{key} = {value}"
            )

    def to_prompt(self):
        return json.dumps(
            self.invariants,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # ЛОКАЛЬНАЯ ПРОВЕРКА КОНФЛИКТОВ
    # --------------------------------------------------------

    def check_conflicts(self, user_message):
        """
        Простая детерминированная проверка
        известных технических конфликтов.

        Возвращает список найденных конфликтов.
        """

        text = user_message.lower()

        conflicts = []

        architecture = str(
            self.invariants.get(
                "architecture",
                ""
            )
        ).lower()

        language = str(
            self.invariants.get(
                "language",
                ""
            )
        ).lower()

        ui = str(
            self.invariants.get(
                "ui",
                ""
            )
        ).lower()

        # Architecture
        if architecture == "mvvm":

            forbidden = [
                "mvp",
                "mvc"
            ]

            for value in forbidden:

                if value in text:
                    conflicts.append(
                        f"architecture=MVVM "
                        f"конфликтует с {value.upper()}"
                    )

        # Language
        if language == "kotlin":

            if (
                "перепиши на java" in text
                or "используй java" in text
                or "пишем на java" in text
                or "сделай на java" in text
            ):
                conflicts.append(
                    "language=Kotlin "
                    "конфликтует с Java"
                )

        # UI
        if (
            "jetpack compose" in ui
            or ui == "compose"
        ):

            if (
                "перепиши на xml" in text
                or "используй xml" in text
                or "сделай на xml" in text
                or "xml layout" in text
            ):
                conflicts.append(
                    "ui=Jetpack Compose "
                    "конфликтует с XML UI"
                )

        return conflicts


# ============================================================
# GEMINI AGENT
# ============================================================

class GeminiAgent:

    def __init__(
        self,
        model="gemini-3.5-flash-lite"
    ):
        self.client = genai.Client()
        self.model = model

        self.task_machine = (
            TaskStateMachine()
        )

        self.invariant_manager = (
            InvariantManager()
        )

        self.last_prompt_tokens = 0
        self.last_response_tokens = 0
        self.last_total_tokens = 0
        self.last_time = 0

    def build_prompt(
        self,
        user_message
    ):
        task_state = (
            self.task_machine.to_prompt()
        )

        invariants = (
            self.invariant_manager.to_prompt()
        )

        return f"""
Ты AI-ассистент, выполняющий задачу пользователя.

У тебя есть формализованное состояние задачи
и отдельный набор обязательных инвариантов.


TASK STATE:

{task_state}


INVARIANTS:

{invariants}


ИНВАРИАНТЫ — обязательные правила.

Ты обязан явно учитывать их при выборе решения.

Нельзя предлагать решение, которое нарушает
хотя бы один инвариант.

Перед формированием ответа:

1. Определи, относится ли запрос к текущей задаче.
2. Проверь запрос на конфликт с INVARIANTS.
3. Если конфликта нет — ответь нормально.
4. Если есть конфликт — не предлагай запрещённое решение.
5. Объясни, какой именно инвариант нарушается.
6. Если возможно, предложи альтернативу,
   которая сохраняет все инварианты.

Не изменяй инварианты самостоятельно.

Запрос пользователя не имеет права автоматически
отменять существующий инвариант.

Изменение инварианта выполняется только отдельной
командой управления состоянием.


Пользователь:

{user_message}


Ассистент:
""".strip()

    def ask(
        self,
        user_message
    ):
        # ----------------------------------------------------
        # УРОВЕНЬ 1:
        # детерминированная проверка Python
        # ----------------------------------------------------

        conflicts = (
            self.invariant_manager
            .check_conflicts(
                user_message
            )
        )

        if conflicts:

            print()
            print("=" * 60)
            print("КОНФЛИКТ С ИНВАРИАНТАМИ")
            print("=" * 60)

            for conflict in conflicts:
                print(
                    f"- {conflict}"
                )

            return (
                "Я не могу предложить это решение, "
                "потому что запрос нарушает "
                "зафиксированные инварианты:\n\n"
                +
                "\n".join(
                    f"- {item}"
                    for item in conflicts
                )
                +
                "\n\nСначала необходимо явно "
                "изменить соответствующий инвариант "
                "либо выбрать решение, которое "
                "ему соответствует."
            )

        # ----------------------------------------------------
        # УРОВЕНЬ 2:
        # Gemini тоже получает все инварианты
        # ----------------------------------------------------

        prompt = self.build_prompt(
            user_message
        )

        print()
        print("-" * 60)
        print("ЗАПРОС К GEMINI")
        print("-" * 60)

        print(
            f"Stage:      "
            f"{self.task_machine.state['stage']}"
        )

        print(
            f"Invariants: "
            f"{len(self.invariant_manager.invariants)}"
        )

        start = time.perf_counter()

        response = (
            self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_level="minimal"
                    )
                )
            )
        )

        self.last_time = (
            time.perf_counter()
            - start
        )

        usage = response.usage_metadata

        self.last_prompt_tokens = (
            usage.prompt_token_count or 0
        )

        self.last_response_tokens = (
            usage.candidates_token_count or 0
        )

        self.last_total_tokens = (
            usage.total_token_count or 0
        )

        print()
        print("-" * 60)
        print("СТАТИСТИКА")
        print("-" * 60)

        print(
            f"Входных токенов:   "
            f"{self.last_prompt_tokens}"
        )

        print(
            f"Токенов ответа:    "
            f"{self.last_response_tokens}"
        )

        print(
            f"Всего токенов API: "
            f"{self.last_total_tokens}"
        )

        print(
            f"Время Gemini:      "
            f"{self.last_time:.2f} сек."
        )

        return response.text


# ============================================================
# COMMAND PARSING
# ============================================================

def parse_key_value(text):
    if "=" not in text:
        return None

    key, value = text.split(
        "=",
        maxsplit=1
    )

    key = key.strip()
    value = value.strip()

    if not key or not value:
        return None

    return key, value


def show_help():
    print()
    print("=" * 60)
    print("ДЕНЬ 14 — INVARIANTS")
    print("=" * 60)

    print("""
TASK STATE

start <задача>
    создать задачу

state
    показать состояние

step <шаг> | <ожидаемое действие>
    установить текущий шаг

next
    следующий этап

pause
    поставить задачу на паузу

resume
    продолжить задачу


INVARIANTS

invariant <ключ>=<значение>
    добавить или изменить инвариант

Пример:
invariant architecture=MVVM

invariants
    показать все инварианты

remove invariant <ключ>
    удалить конкретный инвариант

clear invariants
    удалить все инварианты


OTHER

reset
    сбросить Task State

help
    показать команды

exit
    выход
""")


# ============================================================
# MAIN
# ============================================================

def main():

    agent = GeminiAgent()

    print("=" * 60)
    print(
        "ДЕНЬ 14 — "
        "ИНВАРИАНТЫ И ОГРАНИЧЕНИЯ"
    )
    print("=" * 60)

    print()
    print(
        f"Модель: {agent.model}"
    )

    print()
    print(
        "Task State: task_state.json"
    )

    print(
        "Invariants: invariants.json"
    )

    show_help()

    while True:

        print()

        user_input = input(
            "Вы: "
        ).strip()

        if not user_input:
            continue

        command = user_input.lower()

        # EXIT
        if command == "exit":

            print()
            print("Агент: До свидания!")
            break

        # HELP
        if command == "help":

            show_help()
            continue

        # STATE
        if command == "state":

            agent.task_machine.show()
            continue

        # INVARIANTS
        if command == "invariants":

            agent.invariant_manager.show()
            continue

        # ADD INVARIANT
        if command.startswith(
            "invariant "
        ):

            data = user_input.split(
                maxsplit=1
            )[1]

            result = parse_key_value(
                data
            )

            if result is None:

                print()
                print(
                    "Используй формат:"
                )

                print(
                    "invariant "
                    "architecture=MVVM"
                )

                continue

            key, value = result

            agent.invariant_manager.add(
                key,
                value
            )

            continue

        # REMOVE INVARIANT
        if command.startswith(
            "remove invariant "
        ):

            key = user_input.split(
                maxsplit=2
            )[2].strip()

            agent.invariant_manager.remove(
                key
            )

            continue

        # CLEAR INVARIANTS
        if command == "clear invariants":

            agent.invariant_manager.clear()
            continue

        # NEXT
        if command == "next":

            agent.task_machine.next_stage()
            continue

        # PAUSE
        if command == "pause":

            agent.task_machine.pause()
            continue

        # RESUME
        if command == "resume":

            agent.task_machine.resume()
            continue

        # RESET
        if command == "reset":

            agent.task_machine.reset()
            continue

        # START
        if command.startswith(
            "start "
        ):

            task = user_input.split(
                maxsplit=1
            )[1].strip()

            agent.task_machine.start_task(
                task
            )

            continue

        # STEP
        if command.startswith(
            "step "
        ):

            data = user_input.split(
                maxsplit=1
            )[1]

            if "|" not in data:

                print()
                print(
                    "Используй формат:"
                )

                print(
                    "step <шаг> | "
                    "<ожидаемое действие>"
                )

                continue

            current_step, expected_action = (
                data.split(
                    "|",
                    maxsplit=1
                )
            )

            agent.task_machine.set_step(
                current_step.strip(),
                expected_action.strip()
            )

            continue

        # NORMAL REQUEST
        try:

            answer = agent.ask(
                user_input
            )

            print()
            print("Агент:")
            print(answer)

        except Exception as error:

            print()
            print("Ошибка:")
            print(error)


if __name__ == "__main__":
    main()