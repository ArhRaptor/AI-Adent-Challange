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


def search_products(query: str) -> list[dict]:

    query = query.lower().strip()

    result = []

    for product in PRODUCTS.values():

        searchable_text = (
            f"{product['id']} "
            f"{product['name']} "
            f"{product['warehouse']}"
        ).lower()

        if query in searchable_text:
            result.append(product)

    return result