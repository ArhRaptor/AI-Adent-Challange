import os

from mcp.server import MCPServer

from warehouse_api import search_products


mcp = MCPServer(
    "Warehouse Pipeline MCP",
    instructions=(
        "MCP-сервер для демонстрации "
        "композиции инструментов."
    )
)


# ============================================================
# TOOL 1 — SEARCH
# ============================================================

@mcp.tool()
def search(query: str) -> dict:
    """
    Ищет товары по названию, ID или складу.

    Args:
        query: Поисковый запрос.
    """

    products = search_products(query)

    return {
        "success": True,
        "query": query,
        "count": len(products),
        "products": products
    }


# ============================================================
# TOOL 2 — SUMMARIZE
# ============================================================

@mcp.tool()
def summarize(search_result: dict) -> dict:
    """
    Создаёт текстовую сводку по результату поиска.

    Args:
        search_result:
            Структурированный результат
            инструмента search.
    """

    products = search_result.get(
        "products",
        []
    )

    query = search_result.get(
        "query",
        ""
    )

    if not products:

        summary = (
            f"По запросу «{query}» "
            f"товары не найдены."
        )

        return {
            "success": True,
            "summary": summary,
            "products_count": 0
        }

    total_quantity = sum(
        product["quantity"]
        for product in products
    )

    total_value = sum(
        product["quantity"]
        * product["price"]
        for product in products
    )

    out_of_stock = [
        product["name"]
        for product in products
        if product["quantity"] == 0
    ]

    lines = [
        f"Сводка по запросу: {query}",
        "",
        f"Найдено товаров: {len(products)}",
        f"Общий остаток: {total_quantity}",
        f"Стоимость остатков: {total_value} руб.",
        "",
        "Товары:"
    ]

    for product in products:

        lines.append(
            f"- {product['name']}: "
            f"{product['quantity']} шт., "
            f"{product['price']} руб., "
            f"склад: {product['warehouse']}"
        )

    if out_of_stock:

        lines.append("")
        lines.append(
            "Нет в наличии:"
        )

        for name in out_of_stock:
            lines.append(
                f"- {name}"
            )

    summary = "\n".join(lines)

    return {
        "success": True,
        "summary": summary,
        "products_count": len(products),
        "total_quantity": total_quantity,
        "total_value": total_value,
        "out_of_stock": out_of_stock
    }


# ============================================================
# TOOL 3 — SAVE TO FILE
# ============================================================

@mcp.tool()
def save_to_file(
    content: str,
    filename: str = "warehouse_report.txt"
) -> dict:
    """
    Сохраняет текстовую сводку в файл.

    Args:
        content:
            Текст для сохранения.

        filename:
            Имя выходного файла.
    """

    reports_dir = "reports"

    os.makedirs(
        reports_dir,
        exist_ok=True
    )

    # Не позволяем выйти из reports
    # через путь вроде ../../file.txt

    safe_filename = os.path.basename(
        filename
    )

    file_path = os.path.join(
        reports_dir,
        safe_filename
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

    return {
        "success": True,
        "filename": safe_filename,
        "path": file_path,
        "characters_written": len(content)
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    mcp.run()