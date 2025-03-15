import asyncio
import argparse
import config
from telegram_connector import TelegramConnector


async def main():
    # Настраиваем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Get information about a Telegram entity.")
    parser.add_argument("entity_identifier", help="ID, username, or invite link of the Telegram entity")
    args = parser.parse_args()

    telegram = TelegramConnector(config.API_ID, config.API_HASH, config.PHONE_NUMBER)
    await telegram.connect()

    entity = await telegram.get_entity_info(args.entity_identifier)

    if entity:
        print("Entity Information:")
        print(f"  ID: {entity.id}")

        if hasattr(entity, 'title'):  # Проверяем, есть ли атрибут 'title' (для чатов/каналов)
            print(f"  Title: {entity.title}")
        if hasattr(entity, 'username'): # Проверяем, есть ли атрибут 'username'
            print(f"  Username: {entity.username}")
        if hasattr(entity, 'first_name'):  # Проверяем, есть ли атрибут 'first_name' (для пользователей)
            print(f"  First Name: {entity.first_name}")
        if hasattr(entity, 'last_name'):   # Проверяем, есть ли атрибут 'last_name'
             print(f" Last Name: {entity.last_name}")
        if hasattr(entity, 'phone'):      # Проверяем, есть ли атрибут 'phone'
            print(f"  Phone: {entity.phone}")
        if hasattr(entity, 'about'):   # Проверяем, есть ли атрибут 'about'
            print(f" Bio: {entity.about}")

        # Дополнительная информация в зависимости от типа сущности
        if hasattr(entity, 'participants_count'):  # Для супергрупп и каналов
            print(f"  Participants Count: {entity.participants_count}")
        if hasattr(entity, 'admins_count'):  # Для супергрупп
            print(f"  Admins Count: {entity.admins_count}")
        if hasattr(entity, 'kicked_count'):  # Для супергрупп
            print(f"  Kicked Count: {entity.kicked_count}")
        if hasattr(entity, 'banned_count'):  # Для супергрупп
            print(f"  Banned Count: {entity.banned_count}")

        print(f"  Type: {telegram.get_entity_type(entity)}") # Выводим тип


if __name__ == "__main__":
    asyncio.run(main())
