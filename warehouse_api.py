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


def get_product(
    product_id: int
):

    return PRODUCTS.get(
        product_id
    )