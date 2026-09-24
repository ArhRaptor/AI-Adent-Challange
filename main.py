import anyio
import json

from google import genai
from google.genai import types

from mcp import Client, StdioServerParameters
from mcp.types import TextContent


# ============================================================
# AGENT
# ============================================================

class WarehouseAgent:

    def __init__(
        self,
        model="gemini-3.5-flash-lite"
    ):

        self.gemini = genai.Client()
        self.model = model

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    def ask_gemini(
        self,
        user_message,
        tool_result
    ):

        prompt = f"""
Ты AI-ассистент приложения склада.

Пользователь задал вопрос:

{user_message}


Для ответа был вызван внешний MCP-инструмент.

Результат MCP-инструмента:

{json.dumps(
    tool_result,
    ensure_ascii=False,
    indent=2
)}


Ответь пользователю на основании результата MCP.

Правила:

1. Не придумывай данные о товаре.
2. Используй результат MCP как источник данных.
3. Если success=false, сообщи, что товар не найден.
4. Если товар найден, кратко сообщи:
   - название;
   - количество;
   - цену;
   - склад.
5. Если quantity=0, явно сообщи,
   что товара сейчас нет в наличии.
""".strip()

        response = (
            self.gemini.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_level="minimal"
                    )
                )
            )
        )

        return response.text


# ============================================================
# MCP
# ============================================================

async def main():

    print("=" * 60)
    print("ДЕНЬ 17 — ПЕРВЫЙ MCP TOOL")
    print("=" * 60)

    agent = WarehouseAgent()

    server = StdioServerParameters(
        command="py",
        args=["mcp_server.py"]
    )

    print()
    print("Подключаемся к MCP-серверу...")

    async with Client(server) as client:

        print()
        print("MCP-соединение установлено.")

        # ----------------------------------------------------
        # LIST TOOLS
        # ----------------------------------------------------

        tools_result = await client.list_tools()

        print()
        print("=" * 60)
        print("ДОСТУПНЫЕ MCP TOOLS")
        print("=" * 60)

        for tool in tools_result.tools:

            print()
            print(f"Name: {tool.name}")
            print(
                f"Description: "
                f"{tool.description}"
            )

            print(
                "Input schema:"
            )

            print(
                json.dumps(
                    tool.input_schema,
                    ensure_ascii=False,
                    indent=2
                )
            )

        # ----------------------------------------------------
        # USER INPUT
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("ВЫЗОВ MCP TOOL")
        print("=" * 60)

        print()
        print(
            "Доступные товары для теста: "
            "101, 102, 103"
        )

        print()

        product_input = input(
            "Введите ID товара: "
        ).strip()

        try:

            product_id = int(
                product_input
            )

        except ValueError:

            print()
            print(
                "ID товара должен быть числом."
            )

            return

        # ----------------------------------------------------
        # CALL TOOL
        # ----------------------------------------------------

        print()
        print(
            f"Вызываем MCP tool "
            f"get_product(product_id={product_id})..."
        )

        result = await client.call_tool(
            "get_product",
            {
                "product_id": product_id
            }
        )

        # ----------------------------------------------------
        # READ RESULT
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("СЫРОЙ РЕЗУЛЬТАТ MCP")
        print("=" * 60)

        tool_data = None

        # Сначала пробуем structured_content.

        if result.structured_content:

            tool_data = (
                result.structured_content
            )

            print(
                json.dumps(
                    tool_data,
                    ensure_ascii=False,
                    indent=2
                )
            )

        else:

            # Fallback:
            # читаем TextContent.

            for block in result.content:

                if isinstance(
                    block,
                    TextContent
                ):

                    print(block.text)

                    try:

                        tool_data = (
                            json.loads(
                                block.text
                            )
                        )

                    except json.JSONDecodeError:

                        tool_data = {
                            "raw_result":
                                block.text
                        }

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if result.is_error:

            print()
            print(
                "MCP сообщил об ошибке "
                "при выполнении инструмента."
            )

            return

        if tool_data is None:

            print()
            print(
                "Не удалось получить "
                "результат инструмента."
            )

            return

        # ----------------------------------------------------
        # USE RESULT IN AGENT
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("ПЕРЕДАЁМ РЕЗУЛЬТАТ АГЕНТУ")
        print("=" * 60)

        user_message = (
            f"Расскажи мне о товаре "
            f"с ID {product_id}."
        )

        answer = agent.ask_gemini(
            user_message,
            tool_data
        )

        print()
        print("Агент:")
        print(answer)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    anyio.run(main)