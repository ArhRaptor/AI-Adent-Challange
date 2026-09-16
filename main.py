from google import genai
from google.genai import types

import json
import os
import time


class TaskStateMachine:
    """
    Конечный автомат задачи.

    planning -> execution -> validation -> done
    """

    STATES = [
        "planning",
        "execution",
        "validation",
        "done"
    ]

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
        self.show()

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
            print(
                "Задача уже находится "
                "в состоянии done."
            )
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
                "Проверить полученный результат"
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
        if self.state["paused"]:
            print()
            print("Задача уже на паузе.")
            return

        self.state["paused"] = True
        self.save()

        print()
        print("Задача поставлена на паузу.")

    def resume(self):
        if not self.state["paused"]:
            print()
            print("Задача не находится на паузе.")
            return

        self.state["paused"] = False
        self.save()

        print()
        print("Задача продолжена.")

        print(
            f"Этап: {self.state['stage']}"
        )

        print(
            f"Текущий шаг: "
            f"{self.state['current_step']}"
        )

        print(
            f"Ожидаемое действие: "
            f"{self.state['expected_action']}"
        )

    def reset(self):
        self.state = self.default_state()
        self.save()

        print()
        print("Состояние задачи сброшено.")

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


class GeminiAgent:
    def __init__(
        self,
        model="gemini-3.5-flash-lite"
    ):
        self.client = genai.Client()
        self.model = model

        self.task_machine = TaskStateMachine()

        self.last_prompt_tokens = 0
        self.last_response_tokens = 0
        self.last_total_tokens = 0
        self.last_time = 0

    def build_prompt(self, user_message):
        task_state = (
            self.task_machine.to_prompt()
        )

        return f"""
Ты AI-ассистент, выполняющий задачу пользователя.

У тебя есть формализованное состояние текущей задачи.

TASK STATE:

{task_state}

Поля состояния:

task
- текущая задача

stage
- текущий этап задачи

current_step
- шаг, который выполняется сейчас

expected_action
- действие, которое ожидается следующим

paused
- находится ли задача на паузе


Возможные этапы:

planning
-> execution
-> validation
-> done


Используй TASK STATE как источник информации
о текущем состоянии задачи.

Не проси пользователя повторно объяснять информацию,
которая уже содержится в TASK STATE.

Если задача находится на паузе, не выполняй следующий
этап автоматически. Сообщи, что задача приостановлена.

Пользователь: {user_message}

Ассистент:
""".strip()

    def ask(self, user_message):
        prompt = self.build_prompt(
            user_message
        )

        print()
        print("-" * 60)
        print("ЗАПРОС К GEMINI")
        print("-" * 60)

        print(
            f"Stage:           "
            f"{self.task_machine.state['stage']}"
        )

        print(
            f"Current step:    "
            f"{self.task_machine.state['current_step']}"
        )

        print(
            f"Expected action: "
            f"{self.task_machine.state['expected_action']}"
        )

        print(
            f"Paused:          "
            f"{self.task_machine.state['paused']}"
        )

        start = time.perf_counter()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal"
                )
            )
        )

        self.last_time = (
            time.perf_counter() - start
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


def show_help():
    print()
    print("=" * 60)
    print("ДЕНЬ 13 — TASK STATE MACHINE")
    print("=" * 60)

    print("""
start <задача>
    создать новую задачу

state
    показать состояние задачи

step <текущий шаг> | <ожидаемое действие>
    изменить текущий шаг

next
    перейти на следующий этап

pause
    поставить задачу на паузу

resume
    продолжить задачу

reset
    сбросить состояние задачи

help
    показать команды

exit
    завершить программу


Этапы задачи:

planning
    ↓
execution
    ↓
validation
    ↓
done
""")


def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 13 — TASK STATE MACHINE")
    print("=" * 60)

    print()
    print(
        f"Модель: {agent.model}"
    )

    print()
    print("Состояние загружено из task_state.json")

    agent.task_machine.show()

    show_help()

    while True:

        print()
        user_input = input(
            "Вы: "
        ).strip()

        if not user_input:
            continue

        command = user_input.lower()

        if command == "exit":
            print()
            print("Агент: До свидания!")
            break

        if command == "help":
            show_help()
            continue

        if command == "state":
            agent.task_machine.show()
            continue

        if command == "next":
            agent.task_machine.next_stage()
            continue

        if command == "pause":
            agent.task_machine.pause()
            continue

        if command == "resume":
            agent.task_machine.resume()
            continue

        if command == "reset":
            agent.task_machine.reset()
            continue

        if command.startswith("start "):
            task = user_input.split(
                maxsplit=1
            )[1].strip()

            agent.task_machine.start_task(
                task
            )

            continue

        if command.startswith("step "):
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