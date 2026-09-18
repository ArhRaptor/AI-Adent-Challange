from google import genai
from google.genai import types

import json
import os
import time


# ============================================================
# TASK STATE MACHINE
# ============================================================

class TaskStateMachine:

    STATES = [
        "planning",
        "execution",
        "validation",
        "done"
    ]

    # --------------------------------------------------------
    # РАЗРЕШЁННЫЕ ПЕРЕХОДЫ
    # --------------------------------------------------------

    ALLOWED_TRANSITIONS = {
        "planning": ["execution"],
        "execution": ["validation"],
        "validation": ["done"],
        "done": []
    }

    def __init__(
        self,
        filename="task_state.json"
    ):
        self.filename = filename
        self.state = self.load()

    # --------------------------------------------------------
    # DEFAULT STATE
    # --------------------------------------------------------

    def default_state(self):

        return {
            "task": "",
            "stage": "planning",
            "current_step": "",
            "expected_action": "",
            "paused": False,

            "plan_approved": False,
            "implementation_completed": False,
            "validation_passed": False
        }

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    def load(self):

        if not os.path.exists(
            self.filename
        ):
            return self.default_state()

        try:

            with open(
                self.filename,
                "r",
                encoding="utf-8"
            ) as file:

                loaded = json.load(file)

            # Добавляем новые поля,
            # если остался JSON от предыдущего дня.

            default = self.default_state()

            for key, value in default.items():

                if key not in loaded:
                    loaded[key] = value

            return loaded

        except (
            json.JSONDecodeError,
            OSError
        ):

            return self.default_state()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # START TASK
    # --------------------------------------------------------

    def start_task(
        self,
        task
    ):

        self.state = self.default_state()

        self.state["task"] = task

        self.state["current_step"] = (
            "Подготовить план выполнения задачи"
        )

        self.state["expected_action"] = (
            "Утвердить план"
        )

        self.save()

        print()
        print("Новая задача создана.")

        self.show()

    # --------------------------------------------------------
    # SHOW
    # --------------------------------------------------------

    def show(self):

        print()
        print("=" * 60)
        print("TASK STATE")
        print("=" * 60)

        print(
            f"Задача:                  "
            f"{self.state['task'] or 'не задана'}"
        )

        print(
            f"Этап:                    "
            f"{self.state['stage']}"
        )

        print(
            f"Текущий шаг:             "
            f"{self.state['current_step'] or 'не задан'}"
        )

        print(
            f"Ожидаемое действие:      "
            f"{self.state['expected_action'] or 'не задано'}"
        )

        print(
            f"Пауза:                   "
            f"{self.state['paused']}"
        )

        print()
        print("УСЛОВИЯ ПЕРЕХОДОВ")
        print("-" * 60)

        print(
            f"План утверждён:          "
            f"{self.state['plan_approved']}"
        )

        print(
            f"Реализация завершена:    "
            f"{self.state['implementation_completed']}"
        )

        print(
            f"Валидация пройдена:      "
            f"{self.state['validation_passed']}"
        )

    # --------------------------------------------------------
    # SET STEP
    # --------------------------------------------------------

    def set_step(
        self,
        current_step,
        expected_action
    ):

        self.state["current_step"] = (
            current_step
        )

        self.state["expected_action"] = (
            expected_action
        )

        self.save()

        print()
        print("Текущий шаг обновлён.")

    # --------------------------------------------------------
    # VALIDATE TRANSITION
    # --------------------------------------------------------

    def validate_transition(
        self,
        target_state
    ):

        current = self.state["stage"]

        # Проверяем существование состояния

        if target_state not in self.STATES:

            return (
                False,
                f"Состояние '{target_state}' "
                f"не существует."
            )

        # Нельзя переходить,
        # пока задача на паузе

        if self.state["paused"]:

            return (
                False,
                "Задача находится на паузе. "
                "Сначала выполните resume."
            )

        # Проверяем граф переходов

        allowed = (
            self.ALLOWED_TRANSITIONS.get(
                current,
                []
            )
        )

        if target_state not in allowed:

            return (
                False,
                f"Переход "
                f"{current} -> {target_state} "
                f"запрещён."
            )

        # ----------------------------------------------------
        # BUSINESS RULES
        # ----------------------------------------------------

        if (
            current == "planning"
            and target_state == "execution"
            and not self.state["plan_approved"]
        ):

            return (
                False,
                "Нельзя начать execution: "
                "план ещё не утверждён."
            )

        if (
            current == "execution"
            and target_state == "validation"
            and not self.state[
                "implementation_completed"
            ]
        ):

            return (
                False,
                "Нельзя перейти к validation: "
                "реализация ещё не завершена."
            )

        if (
            current == "validation"
            and target_state == "done"
            and not self.state[
                "validation_passed"
            ]
        ):

            return (
                False,
                "Нельзя завершить задачу: "
                "валидация ещё не пройдена."
            )

        return (
            True,
            "Переход разрешён."
        )

    # --------------------------------------------------------
    # TRANSITION
    # --------------------------------------------------------

    def transition_to(
        self,
        target_state
    ):

        target_state = (
            target_state
            .strip()
            .lower()
        )

        current = self.state["stage"]

        allowed, reason = (
            self.validate_transition(
                target_state
            )
        )

        if not allowed:

            print()
            print("=" * 60)
            print("ПЕРЕХОД ЗАБЛОКИРОВАН")
            print("=" * 60)

            print()
            print(
                f"Текущее состояние: {current}"
            )

            print(
                f"Запрошено:         {target_state}"
            )

            print()
            print(
                f"Причина: {reason}"
            )

            return False

        # Переход разрешён

        self.state["stage"] = (
            target_state
        )

        self.update_stage_description()

        self.save()

        print()
        print("=" * 60)
        print("ПЕРЕХОД ВЫПОЛНЕН")
        print("=" * 60)

        print()
        print(
            f"{current} -> {target_state}"
        )

        return True

    # --------------------------------------------------------
    # NEXT
    # --------------------------------------------------------

    def next_stage(self):

        current = self.state["stage"]

        allowed = (
            self.ALLOWED_TRANSITIONS.get(
                current,
                []
            )
        )

        if not allowed:

            print()
            print(
                "Следующего состояния нет."
            )

            return False

        # В нашей модели у каждого состояния
        # только один следующий этап.

        target = allowed[0]

        return self.transition_to(
            target
        )

    # --------------------------------------------------------
    # UPDATE DESCRIPTION
    # --------------------------------------------------------

    def update_stage_description(self):

        stage = self.state["stage"]

        if stage == "planning":

            self.state["current_step"] = (
                "Подготовить план выполнения задачи"
            )

            self.state["expected_action"] = (
                "Утвердить план"
            )

        elif stage == "execution":

            self.state["current_step"] = (
                "Выполнить реализацию"
            )

            self.state["expected_action"] = (
                "Завершить реализацию"
            )

        elif stage == "validation":

            self.state["current_step"] = (
                "Проверить результат"
            )

            self.state["expected_action"] = (
                "Подтвердить успешную валидацию"
            )

        elif stage == "done":

            self.state["current_step"] = (
                "Задача завершена"
            )

            self.state["expected_action"] = (
                "Никаких действий не требуется"
            )

    # --------------------------------------------------------
    # APPROVE PLAN
    # --------------------------------------------------------

    def approve_plan(self):

        if self.state["stage"] != "planning":

            print()
            print(
                "План можно утверждать "
                "только на этапе planning."
            )

            return

        self.state["plan_approved"] = True

        self.state["expected_action"] = (
            "Перейти к execution"
        )

        self.save()

        print()
        print("План утверждён.")

    # --------------------------------------------------------
    # COMPLETE IMPLEMENTATION
    # --------------------------------------------------------

    def complete_implementation(self):

        if self.state["stage"] != "execution":

            print()
            print(
                "Завершить реализацию можно "
                "только на этапе execution."
            )

            return

        self.state[
            "implementation_completed"
        ] = True

        self.state["expected_action"] = (
            "Перейти к validation"
        )

        self.save()

        print()
        print("Реализация отмечена завершённой.")

    # --------------------------------------------------------
    # PASS VALIDATION
    # --------------------------------------------------------

    def pass_validation(self):

        if self.state["stage"] != "validation":

            print()
            print(
                "Валидацию можно подтвердить "
                "только на этапе validation."
            )

            return

        self.state[
            "validation_passed"
        ] = True

        self.state["expected_action"] = (
            "Перейти к done"
        )

        self.save()

        print()
        print("Валидация успешно пройдена.")

    # --------------------------------------------------------
    # PAUSE
    # --------------------------------------------------------

    def pause(self):

        if self.state["paused"]:

            print()
            print(
                "Задача уже находится на паузе."
            )

            return

        self.state["paused"] = True

        self.save()

        print()
        print("Задача поставлена на паузу.")

    # --------------------------------------------------------
    # RESUME
    # --------------------------------------------------------

    def resume(self):

        if not self.state["paused"]:

            print()
            print(
                "Задача не находится на паузе."
            )

            return

        self.state["paused"] = False

        self.save()

        print()
        print("Задача продолжена.")

        print(
            f"Продолжаем с этапа: "
            f"{self.state['stage']}"
        )

        print(
            f"Текущий шаг: "
            f"{self.state['current_step']}"
        )

        print(
            f"Ожидаемое действие: "
            f"{self.state['expected_action']}"
        )

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    def reset(self):

        self.state = self.default_state()

        self.save()

        print()
        print("Task State сброшен.")

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    def to_prompt(self):

        return json.dumps(
            self.state,
            ensure_ascii=False,
            indent=2
        )


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

        self.last_prompt_tokens = 0
        self.last_response_tokens = 0
        self.last_total_tokens = 0
        self.last_time = 0

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    def build_prompt(
        self,
        user_message
    ):

        task_state = (
            self.task_machine.to_prompt()
        )

        return f"""
Ты AI-ассистент с контролируемым жизненным циклом задачи.

Текущее формализованное состояние:

TASK STATE:

{task_state}


Разрешённый жизненный цикл:

planning
->
execution
->
validation
->
done


Правила:

1. Нельзя выполнять реализацию,
   пока план не утверждён.

2. Нельзя переходить к validation,
   пока реализация не завершена.

3. Нельзя считать задачу done,
   пока validation не пройдена.

4. Нельзя перепрыгивать состояния.

5. Если задача paused,
   нельзя продолжать выполнение,
   пока пользователь явно не выполнит resume.

6. Не изменяй состояние задачи самостоятельно.

7. Управление состоянием выполняется
   только через команды программы.

8. Если запрос пользователя требует действия,
   которое невозможно на текущем этапе,
   объясни, почему оно сейчас недоступно
   и какое действие необходимо выполнить сначала.

Используй TASK STATE как источник истины
о текущем жизненном цикле задачи.


Пользователь:

{user_message}


Ассистент:
""".strip()

    # --------------------------------------------------------
    # ASK
    # --------------------------------------------------------

    def ask(
        self,
        user_message
    ):

        prompt = self.build_prompt(
            user_message
        )

        print()
        print("-" * 60)
        print("ЗАПРОС К GEMINI")
        print("-" * 60)

        print(
            f"Stage:  "
            f"{self.task_machine.state['stage']}"
        )

        print(
            f"Paused: "
            f"{self.task_machine.state['paused']}"
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
# HELP
# ============================================================

def show_help():

    print()
    print("=" * 60)
    print("ДЕНЬ 15 — CONTROLLED TRANSITIONS")
    print("=" * 60)

    print("""
TASK

start <задача>
    создать новую задачу

state
    показать состояние


LIFECYCLE

approve plan
    утвердить план

complete implementation
    отметить реализацию завершённой

pass validation
    подтвердить успешную валидацию

next
    перейти на следующий разрешённый этап

goto <state>
    попытаться явно перейти в состояние


PAUSE

pause
    поставить задачу на паузу

resume
    продолжить задачу


OTHER

step <шаг> | <ожидаемое действие>
    изменить описание текущего шага

reset
    сбросить состояние

help
    показать команды

exit
    завершить программу


Жизненный цикл:

planning
    ↓
execution
    ↓
validation
    ↓
done
""")


# ============================================================
# MAIN
# ============================================================

def main():

    agent = GeminiAgent()

    print("=" * 60)
    print(
        "ДЕНЬ 15 — "
        "КОНТРОЛИРУЕМЫЕ ПЕРЕХОДЫ"
    )
    print("=" * 60)

    print()
    print(
        f"Модель: {agent.model}"
    )

    print()
    print(
        "Состояние: task_state.json"
    )

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

        # RESET
        if command == "reset":

            agent.task_machine.reset()
            continue

        # START
        if command.startswith("start "):

            task = user_input.split(
                maxsplit=1
            )[1].strip()

            agent.task_machine.start_task(
                task
            )

            continue

        # APPROVE PLAN
        if command == "approve plan":

            agent.task_machine.approve_plan()
            continue

        # COMPLETE IMPLEMENTATION
        if command == "complete implementation":

            agent.task_machine.complete_implementation()
            continue

        # PASS VALIDATION
        if command == "pass validation":

            agent.task_machine.pass_validation()
            continue

        # NEXT
        if command == "next":

            agent.task_machine.next_stage()
            continue

        # GOTO
        if command.startswith("goto "):

            target = command.split(
                maxsplit=1
            )[1]

            agent.task_machine.transition_to(
                target
            )

            continue

        # PAUSE
        if command == "pause":

            agent.task_machine.pause()
            continue

        # RESUME
        if command == "resume":

            agent.task_machine.resume()
            continue

        # STEP
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