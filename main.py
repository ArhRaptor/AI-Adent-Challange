import anyio
import json

from google import genai
from google.genai import types

from mcp import (
    Client,
    StdioServerParameters
)


# ============================================================
# AGENT
# ============================================================

class WarehouseAgent:

    def __init__(
        self,
        model="gemini-3.5-flash-lite"
    ):

        self.client = genai.Client()
        self.model = model

    def create_summary(
        self,
        tool_result
    ):

        prompt = f"""
Ты AI-ассистент системы мониторинга склада.

Ниже находится агрегированный результат,
полученный через MCP-инструмент:

{json.dumps(
    tool_result,
    ensure_ascii=False,
    indent=2
)}

Сформируй краткую понятную сводку.

Укажи:

- название товара;
- количество измерений;
- текущий остаток;
- минимальный остаток;
- максимальный остаток;
- средний остаток;
- время последнего измерения.

Не придумывай отсутствующие данные.
""".strip()

        response = (
            self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=
                        types.ThinkingConfig(
                            thinking_level="minimal"
                        )
                )
            )
        )

        return response.text


# ============================================================
# MCP RESULT
# ============================================================

def get_structured_result(
    result
):

    if result.structured_content:

        return result.structured_content

    # Fallback

    for block in result.content:

        if hasattr(
            block,
            "text"
        ):

            try:

                return json.loads(
                    block.text
                )

            except json.JSONDecodeError:

                return {
                    "raw_result":
                        block.text
                }

    return None


# ============================================================
# MAIN
# ============================================================

async def main():

    print("=" * 60)
    print(
        "ДЕНЬ 18 — MCP SCHEDULER"
    )
    print("=" * 60)

    agent = WarehouseAgent()

    server = StdioServerParameters(
        command="py",
        args=["mcp_server.py"]
    )

    async with Client(
        server
    ) as client:

        print()
        print(
            "MCP-соединение установлено."
        )

        print()
        print(
            "1 — Создать мониторинг"
        )

        print(
            "2 — Показать задачи"
        )

        print(
            "3 — Получить сводку"
        )

        print()

        choice = input(
            "Выберите действие: "
        ).strip()

        # ====================================================
        # CREATE TASK
        # ====================================================

        if choice == "1":

            product_id = int(
                input(
                    "ID товара: "
                )
            )

            interval = int(
                input(
                    "Интервал в секундах: "
                )
            )

            result = await client.call_tool(
                "create_monitoring_task",
                {
                    "product_id":
                        product_id,

                    "interval_seconds":
                        interval
                }
            )

            data = get_structured_result(
                result
            )

            print()
            print("=" * 60)
            print("РЕЗУЛЬТАТ")
            print("=" * 60)

            print(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )
            )

        # ====================================================
        # LIST
        # ====================================================

        elif choice == "2":

            result = await client.call_tool(
                "list_tasks",
                {}
            )

            data = get_structured_result(
                result
            )

            print()
            print("=" * 60)
            print("ЗАДАЧИ")
            print("=" * 60)

            print(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )
            )

        # ====================================================
        # SUMMARY
        # ====================================================

        elif choice == "3":

            product_id = int(
                input(
                    "ID товара: "
                )
            )

            result = await client.call_tool(
                "get_summary",
                {
                    "product_id":
                        product_id
                }
            )

            data = get_structured_result(
                result
            )

            print()
            print("=" * 60)
            print("MCP SUMMARY")
            print("=" * 60)

            print(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )
            )

            if (
                data
                and data.get(
                    "success"
                )
            ):

                print()
                print("=" * 60)
                print("AGENT SUMMARY")
                print("=" * 60)

                answer = (
                    agent.create_summary(
                        data
                    )
                )

                print()
                print(answer)

            else:

                print()
                print(
                    "Данных для сводки "
                    "пока недостаточно."
                )

        else:

            print()
            print(
                "Неизвестная команда."
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    anyio.run(main)