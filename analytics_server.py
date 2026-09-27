from mcp.server import MCPServer


mcp = MCPServer(
    "Analytics MCP Server",
    instructions=(
        "Сервер анализирует данные "
        "о товарах."
    )
)


@mcp.tool()
def analyze_products(
    products: list[dict]
) -> dict:
    """
    Анализирует список товаров.

    Рассчитывает количество товаров,
    остатки и стоимость склада.
    """

    if not products:

        return {
            "success": True,
            "products_count": 0,
            "total_quantity": 0,
            "total_value": 0,
            "out_of_stock": [],
            "report": (
                "Нет товаров для анализа."
            )
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
        "Аналитический отчёт",
        "",
        (
            f"Количество товаров: "
            f"{len(products)}"
        ),
        (
            f"Общий остаток: "
            f"{total_quantity}"
        ),
        (
            f"Стоимость остатков: "
            f"{total_value} руб."
        ),
        "",
        "Товары:"
    ]

    for product in products:

        lines.append(
            f"- {product['name']}: "
            f"{product['quantity']} шт., "
            f"{product['price']} руб., "
            f"{product['warehouse']}"
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

    report = "\n".join(lines)

    return {
        "success": True,
        "products_count": len(products),
        "total_quantity": total_quantity,
        "total_value": total_value,
        "out_of_stock": out_of_stock,
        "report": report
    }


if __name__ == "__main__":
    mcp.run()