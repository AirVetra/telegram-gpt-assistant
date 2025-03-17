import asyncio
import argparse
import config
from telegram_connector import TelegramConnector
#Убираем from telethon.utils import get_peer_id  #  get_peer_id  теперь тут не нужен


async def main():
    # Настраиваем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Search for Telegram entities by ID, username, phone, name, or title.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user", help="Username of the Telegram entity")
    group.add_argument("--tel", help="Phone number of the Telegram entity")
    group.add_argument("--id", help="ID of the Telegram entity")
    group.add_argument("--first_name", help="First name for searching contacts")
    group.add_argument("--last_name", help="Last name for searching contacts")
    group.add_argument("--title", help="Title for searching dialogs")

    args = parser.parse_args()

    telegram = TelegramConnector(config.API_ID, config.API_HASH, config.PHONE_NUMBER)
    await telegram.connect()

    # Вызываем search_entities с нужными аргументами
    results = await telegram.search_entities(
        id=args.id,
        user=args.user,
        tel=args.tel,
        first_name=args.first_name,
        last_name=args.last_name,
        title=args.title
    )

    # Выводим результаты
    if results:
        print("Search Results:")
        for entity in results:
            print_entity_info(entity, telegram) #Передаем список
            print("---")
    else:
        print("No entities found matching the search criteria.")


def print_entity_info(entity, telegram): #Убираем telegram
    if entity:
        print("Entity Information:")
        print(f"  Full ID: {entity.full_id}")  # Используем атрибут full_id
        print(f"  ID: {entity.id}")

        if hasattr(entity, 'title'):
            print(f"  Title: {entity.title}")
        if hasattr(entity, 'username'):
            print(f"  Username: {entity.username}")
        if hasattr(entity, 'first_name'):
            print(f"  First Name: {entity.first_name}")
        if hasattr(entity, 'last_name'):
            print(f"  Last Name: {entity.last_name}")
        if hasattr(entity, 'phone'):
            print(f"  Phone: {entity.phone}")
        if hasattr(entity, 'about'):
            print(f"  Bio: {entity.about}")
        if hasattr(entity, 'access_hash'): #Добавил вывод access_hash
            print(f" Access Hash: {entity.access_hash}")

        # Дополнительная информация в зависимости от типа сущности
        if hasattr(entity, 'participants_count'):
            print(f"  Participants Count: {entity.participants_count}")
        if hasattr(entity, 'admins_count'):
            print(f"  Admins Count: {entity.admins_count}")
        if hasattr(entity, 'kicked_count'):
            print(f"  Kicked Count: {entity.kicked_count}")
        if hasattr(entity, 'banned_count'):
            print(f"  Banned Count: {entity.banned_count}")

        print(f"  Type: {telegram.get_entity_type(entity)}")

    #else:  #Убрал, так как выводится в main
        #print("Entity not found.")

if __name__ == "__main__":
    asyncio.run(main())
