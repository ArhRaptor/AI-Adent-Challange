from mcp.server import MCPServer


mcp = MCPServer(
    "Warehouse MCP Server",
    instructions=(
        "Сервер предоставляет инструменты "
        "для поиска товаров на складе."
    )
)


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
    },

    104: {
        "id": 104,
        "name": "Мышь Logitech",
        "quantity": 15,
        "price": 3500,
        "warehouse": "Москва"
    }
}


# ============================================================
# SEARCH
# ============================================================

@mcp.tool()
def search_products(query: str) -> dict:
    """
    Ищет товары по названию,
    ID или складу.
    """

    query_lower = query.lower().strip()

    products = []

    for product in PRODUCTS.values():

        searchable = (
            f"{product['id']} "
            f"{product['name']} "
            f"{product['warehouse']}"
        ).lower()

        if query_lower in searchable:
            products.append(product)

    return {
        "success": True,
        "query": query,
        "count": len(products),
        "products": products
    }


# ============================================================
# GET PRODUCT
# ============================================================

@mcp.tool()
def get_product(product_id: int) -> dict:
    """
    Возвращает товар по ID.
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


if __name__ == "__main__":
    mcp.run()