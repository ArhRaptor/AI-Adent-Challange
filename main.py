import anyio
import json

from google import genai
from google.genai import types

from mcp import (
    Client,
    StdioServerParameters
)


# ============================================================
# MCP RESULT
# ============================================================

def get_result(result):

    if result.is_error:
        return None

    if result.structured_content:
        return result.structured_content

    for block in result.content:

        if hasattr(block, "text"):

            try:
                return json.loads(
                    block.text
                )

            except json.JSONDecodeError:

                return {
                    "text": block.text
                }

    return None


# ============================================================
# ROUTER
# ============================================================

class AgentRouter:

    def __init__(self):

        self.client = genai.Client()

        self.model = (
            "gemini-3.5-flash-lite"
        )

    def route(
        self,
        user_message
    ):

        prompt = f"""
Ты маршрутизатор MCP-инструментов.

Доступны три типа операций:

1. search
   Используй, если пользователь хочет
   найти или показать товары.

2. analyze
   Используй, если пользователь хочет
   найти товары и провести анализ.

3. full_report
   Используй, если пользователь хочет:
   найти товары,
   проанализировать их
   и сохранить отчёт.

Верни ТОЛЬКО JSON.

Формат:

{{
  "route": "search | analyze | full_report",
  "query": "поисковый запрос"
}}

Примеры:

"Найди товары в Москве"

{{
  "route": "search",
  "query": "Москва"
}}

"Проанализируй товары Logitech"

{{
  "route": "analyze",
  "query": "Logitech"
}}

"Найди товары в Москве,
проанализируй остатки
и сохрани отчёт"

{{
  "route": "full_report",
  "query": "Москва"
}}

Запрос пользователя:

{user_message}
""".strip()

        response = (
            self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type=(
                        "application/json"
                    ),
                    thinking_config=
                        types.ThinkingConfig(
                            thinking_level="minimal"
                        )
                )
            )
        )

        return json.loads(
            response.text
        )


# ============================================================
# SEARCH
# ============================================================

async def search_step(
    warehouse_client,
    query
):

    print()
    print("=" * 60)
    print(
        "SERVER: WAREHOUSE"
    )
    print(
        "TOOL: search_products"
    )
    print("=" * 60)

    result = await warehouse_client.call_tool(
        "search_products",
        {
            "query": query
        }
    )

    data = get_result(result)

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )

    return data


# ============================================================
# ANALYTICS
# ============================================================

async def analytics_step(
    analytics_client,
    products
):

    print()
    print("=" * 60)
    print(
        "SERVER: ANALYTICS"
    )
    print(
        "TOOL: analyze_products"
    )
    print("=" * 60)

    result = await analytics_client.call_tool(
        "analyze_products",
        {
            "products": products
        }
    )

    data = get_result(result)

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )

    return data


# ============================================================
# SAVE
# ============================================================

async def save_step(
    report_client,
    report
):

    print()
    print("=" * 60)
    print(
        "SERVER: REPORT"
    )
    print(
        "TOOL: save_report"
    )
    print("=" * 60)

    result = await report_client.call_tool(
        "save_report",
        {
            "content": report,
            "filename":
                "warehouse_report.txt"
        }
    )

    data = get_result(result)

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )

    return data


# ============================================================
# ORCHESTRATOR
# ============================================================

async def orchestrate(
    route,
    query,
    warehouse_client,
    analytics_client,
    report_client
):

    # --------------------------------------------------------
    # STEP 1
    # Warehouse Server
    # --------------------------------------------------------

    search_data = await search_step(
        warehouse_client,
        query
    )

    if not search_data:

        print(
            "Ошибка на этапе поиска."
        )

        return

    # Только поиск
    if route == "search":

        print()
        print("=" * 60)
        print("FLOW COMPLETED")
        print("=" * 60)

        print(
            "Маршрут: Warehouse"
        )

        return

    # --------------------------------------------------------
    # STEP 2
    # Analytics Server
    # --------------------------------------------------------

    analytics_data = (
        await analytics_step(
            analytics_client,
            search_data.get(
                "products",
                []
            )
        )
    )

    if not analytics_data:

        print(
            "Ошибка на этапе анализа."
        )

        return

    # Поиск + анализ
    if route == "analyze":

        print()
        print("=" * 60)
        print("FLOW COMPLETED")
        print("=" * 60)

        print(
            "Маршрут:"
        )

        print(
            "Warehouse → Analytics"
        )

        return

    # --------------------------------------------------------
    # STEP 3
    # Report Server
    # --------------------------------------------------------

    if route == "full_report":

        save_data = await save_step(
            report_client,
            analytics_data.get(
                "report",
                ""
            )
        )

        if not save_data:

            print(
                "Ошибка сохранения."
            )

            return

        print()
        print("=" * 60)
        print("FLOW COMPLETED")
        print("=" * 60)

        print(
            "Маршрут:"
        )

        print(
            "Warehouse"
            " → Analytics"
            " → Report"
        )

        print()

        print(
            f"Отчёт сохранён: "
            f"{save_data['path']}"
        )

        return

    print(
        f"Неизвестный маршрут: "
        f"{route}"
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    print("=" * 60)
    print(
        "ДЕНЬ 20 — MCP ORCHESTRATION"
    )
    print("=" * 60)

    router = AgentRouter()

    # --------------------------------------------------------
    # THREE MCP SERVERS
    # --------------------------------------------------------

    warehouse_server = (
        StdioServerParameters(
            command="py",
            args=[
                "warehouse_server.py"
            ]
        )
    )

    analytics_server = (
        StdioServerParameters(
            command="py",
            args=[
                "analytics_server.py"
            ]
        )
    )

    report_server = (
        StdioServerParameters(
            command="py",
            args=[
                "report_server.py"
            ]
        )
    )

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    async with Client(
        warehouse_server
    ) as warehouse_client:

        async with Client(
            analytics_server
        ) as analytics_client:

            async with Client(
                report_server
            ) as report_client:

                print()
                print(
                    "Подключено MCP-серверов: 3"
                )

                print(
                    "- Warehouse"
                )

                print(
                    "- Analytics"
                )

                print(
                    "- Report"
                )

                # --------------------------------------------
                # USER REQUEST
                # --------------------------------------------

                print()

                user_message = input(
                    "Вы: "
                ).strip()

                if not user_message:
                    return

                # --------------------------------------------
                # AGENT ROUTING
                # --------------------------------------------

                decision = router.route(
                    user_message
                )

                route = decision.get(
                    "route"
                )

                query = decision.get(
                    "query",
                    ""
                )

                print()
                print("=" * 60)
                print("AGENT ROUTER")
                print("=" * 60)

                print(
                    f"Route: {route}"
                )

                print(
                    f"Query: {query}"
                )

                # --------------------------------------------
                # FLOW
                # --------------------------------------------

                await orchestrate(
                    route,
                    query,
                    warehouse_client,
                    analytics_client,
                    report_client
                )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    anyio.run(main)