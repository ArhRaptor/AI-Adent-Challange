import anyio

from mcp import Client, StdioServerParameters


async def main():

    print("=" * 60)
    print("ДЕНЬ 16 — MCP CLIENT")
    print("=" * 60)

    # Описываем локальный MCP-сервер.
    #
    # Клиент сам запустит:
    #
    # py mcp_server.py

    server = StdioServerParameters(
        command="py",
        args=["mcp_server.py"]
    )

    print()
    print("Подключаемся к MCP-серверу...")

    try:

        # Вход в async with:
        #
        # 1. запускает MCP-сервер;
        # 2. устанавливает соединение;
        # 3. выполняет MCP handshake.

        async with Client(server) as client:

            print()
            print("MCP-соединение установлено.")

            # Информация о соединении

            print()
            print("-" * 60)
            print("ИНФОРМАЦИЯ О СЕРВЕРЕ")
            print("-" * 60)

            if client.server_info:

                print(
                    f"Имя: "
                    f"{client.server_info.name}"
                )

                print(
                    f"Версия: "
                    f"{client.server_info.version}"
                )

            print(
                f"Версия протокола: "
                f"{client.protocol_version}"
            )

            # --------------------------------------------
            # Получаем инструменты
            # --------------------------------------------

            print()
            print("Запрашиваем список инструментов...")

            result = await client.list_tools()

            tools = result.tools

            print()
            print("=" * 60)
            print("ДОСТУПНЫЕ MCP TOOLS")
            print("=" * 60)

            if not tools:

                print()
                print("Инструменты не найдены.")

            else:

                print()
                print(
                    f"Количество инструментов: "
                    f"{len(tools)}"
                )

                for index, tool in enumerate(
                    tools,
                    start=1
                ):

                    print()
                    print("-" * 60)

                    print(
                        f"TOOL #{index}"
                    )

                    print(
                        f"Name: "
                        f"{tool.name}"
                    )

                    print(
                        f"Title: "
                        f"{tool.title}"
                    )

                    print(
                        f"Description: "
                        f"{tool.description}"
                    )

                    print(
                        f"Input schema: "
                        f"{tool.input_schema}"
                    )

            print()
            print("=" * 60)
            print("ПРОВЕРКА ЗАВЕРШЕНА")
            print("=" * 60)

            print()
            print(
                "MCP-клиент успешно получил "
                "список инструментов."
            )

    except Exception as error:

        print()
        print("=" * 60)
        print("ОШИБКА MCP")
        print("=" * 60)

        print()
        print(error)


if __name__ == "__main__":
    anyio.run(main)