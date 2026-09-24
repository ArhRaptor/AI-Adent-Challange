import anyio
import json

from mcp import (
    Client,
    StdioServerParameters
)


# ============================================================
# RESULT HELPER
# ============================================================

def get_result(result) -> dict | None:

    if result.is_error:

        print(
            "MCP Tool вернул ошибку."
        )

        return None

    if result.structured_content:

        return result.structured_content

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
                    "text": block.text
                }

    return None


# ============================================================
# PIPELINE
# ============================================================

async def run_pipeline(
    client,
    query: str
):

    print()
    print("=" * 60)
    print("MCP PIPELINE")
    print("=" * 60)

    # ========================================================
    # STEP 1
    # SEARCH
    # ========================================================

    print()
    print("[1/3] SEARCH")
    print("-" * 60)

    search_response = (
        await client.call_tool(
            "search",
            {
                "query": query
            }
        )
    )

    search_result = get_result(
        search_response
    )

    if search_result is None:
        print(
            "Pipeline остановлен "
            "на этапе search."
        )
        return

    print(
        json.dumps(
            search_result,
            ensure_ascii=False,
            indent=2
        )
    )

    # ========================================================
    # STEP 2
    # SUMMARIZE
    # ========================================================

    print()
    print("[2/3] SUMMARIZE")
    print("-" * 60)

    print(
        "Передаём результат search "
        "в summarize..."
    )

    summarize_response = (
        await client.call_tool(
            "summarize",
            {
                "search_result":
                    search_result
            }
        )
    )

    summary_result = get_result(
        summarize_response
    )

    if summary_result is None:
        print(
            "Pipeline остановлен "
            "на этапе summarize."
        )
        return

    print()
    print(
        summary_result.get(
            "summary"
        )
    )

    # ========================================================
    # STEP 3
    # SAVE
    # ========================================================

    print()
    print("[3/3] SAVE TO FILE")
    print("-" * 60)

    print(
        "Передаём результат summarize "
        "в save_to_file..."
    )

    summary_text = (
        summary_result.get(
            "summary",
            ""
        )
    )

    save_response = (
        await client.call_tool(
            "save_to_file",
            {
                "content":
                    summary_text,

                "filename":
                    "warehouse_report.txt"
            }
        )
    )

    save_result = get_result(
        save_response
    )

    if save_result is None:
        print(
            "Pipeline остановлен "
            "на этапе save_to_file."
        )
        return

    print(
        json.dumps(
            save_result,
            ensure_ascii=False,
            indent=2
        )
    )

    # ========================================================
    # DONE
    # ========================================================

    print()
    print("=" * 60)
    print("PIPELINE COMPLETED")
    print("=" * 60)

    print()
    print(
        f"Search: "
        f"{search_result['count']} товаров"
    )

    print(
        f"Summary: "
        f"{summary_result['products_count']} товаров"
    )

    print(
        f"Saved: "
        f"{save_result['path']}"
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    print("=" * 60)
    print(
        "ДЕНЬ 19 — MCP TOOL COMPOSITION"
    )
    print("=" * 60)

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

        # ----------------------------------------------------
        # Показываем доступные tools
        # ----------------------------------------------------

        tools = await client.list_tools()

        print()
        print("Доступные инструменты:")

        for tool in tools.tools:
            print(
                f"- {tool.name}"
            )

        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        print()

        query = input(
            "Что ищем: "
        ).strip()

        if not query:

            print(
                "Поисковый запрос пуст."
            )

            return

        # ----------------------------------------------------
        # AUTOMATIC PIPELINE
        # ----------------------------------------------------

        await run_pipeline(
            client,
            query
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    anyio.run(main)