from mcp.server import MCPServer


mcp = MCPServer(
    "Warehouse MCP Server",
    instructions="MCP-сервер для работы с товарами склада."
)


# ============================================================
# MOCK API
# ============================================================

PRODUCTS = {
    101: {
        "id": 101,
        "name": "Ноутбук Lenovo ThinkBook",
        "quantity": 7,
        "price": 85000,
        "warehouse": "Москва"
    },

    102: {
        "id": 102,
        "name": "Монитор Samsung 27",
        "quantity": 0,
        "price": 32000,
        "warehouse": "Москва"
    },

    103: {
        "id": 103,
        "name": "Клавиатура Logitech",
        "quantity": 24,
        "price": 6500,
        "warehouse": "Санкт-Петербург"
    }
}


# ============================================================
# MCP TOOL
# ============================================================

@mcp.tool(
    title="Получить товар",
    description=(
        "Возвращает информацию о товаре "
        "на складе по его ID."
    )
)
def get_product(product_id: int) -> dict:
    """
    Получает товар из mock API склада.

    Args:
        product_id:
            Уникальный числовой ID товара.
    """

    product = PRODUCTS.get(product_id)

    if product is None:
        return {
            "success": False,
            "error": "Товар не найден",
            "product_id": product_id
        }

    return {
        "success": True,
        "product": product
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    mcp.run()