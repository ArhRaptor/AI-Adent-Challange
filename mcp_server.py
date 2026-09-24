from mcp.server import MCPServer


mcp = MCPServer(
    "Day 16 MCP Server",
    instructions="Учебный MCP-сервер для Дня 16."
)


@mcp.tool(
    title="Calculator"
)
def add(a: int, b: int) -> int:
    """
    Складывает два числа.
    """
    return a + b


@mcp.tool(
    title="Greeting"
)
def greet(name: str) -> str:
    """
    Возвращает приветствие.
    """
    return f"Привет, {name}!"


if __name__ == "__main__":
    mcp.run()