import os

from mcp.server import MCPServer


mcp = MCPServer(
    "Report MCP Server",
    instructions=(
        "Сервер сохраняет отчёты "
        "в локальные файлы."
    )
)


@mcp.tool()
def save_report(
    content: str,
    filename: str = "warehouse_report.txt"
) -> dict:
    """
    Сохраняет отчёт в файл.
    """

    directory = "reports"

    os.makedirs(
        directory,
        exist_ok=True
    )

    safe_filename = os.path.basename(
        filename
    )

    path = os.path.join(
        directory,
        safe_filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

    return {
        "success": True,
        "filename": safe_filename,
        "path": path,
        "characters_written": len(content)
    }


if __name__ == "__main__":
    mcp.run()