import asyncio
import argparse
import config
from telegram_connector import TelegramConnector
from telethon.utils import get_peer_id


async def main():
    print("--- STARTING MAIN ---")  # Добавляем

    # Настраиваем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Search for Telegram entities by ID, username, phone, name, or title.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user", help="Username of the Telegram entity")
    group.add_argument("--tel", help="Phone number of the Telegram entity")
    group.add_argument("--id", help="ID of the Telegram entity")
    group.add_argument("--first_name", help="First name for searching contacts")
    group.add_argument("--last_name", help="Last name for searching contacts")
    group.add_argument("--title", help="Title for searching dialogs")
    group.add_argument("--recent_messages", help="Get recent messages from the specified entity (ID, username, or phone)")
    parser.add_argument("--limit", help="How many messages you want to get (only with --recent_messages)", type=int, default=1) #Добавил

    args = parser.parse_args()
    print(f"Parsed arguments: {args}")  # Добавляем

    telegram = TelegramConnector(config.API_ID, config.API_HASH, config.PHONE_NUMBER)
    await telegram.connect()
    print("Telegram connector connected.") # Добавляем

    if args.first_name or args.last_name:
        # Поиск по имени/фамилии
        print("Searching by first/last name...") # Добавляем
        results = await telegram.search_entities(first_name=args.first_name, last_name=args.last_name)
        if results:
            print("Search Results:")
            for user in results:
                print_entity_info(user) #Убрал telegram
                print("---")
        else:
            print("No entities found matching the search criteria.")

    elif args.user:
        # Получение информации по username
        print(f"Searching by username: {args.user}") # Добавляем
        results = await telegram.search_entities(user=args.user)
        if results:
            print_entity_info(results[0]) #Убрал telegram
        else:
            print("Entity not found.")


    elif args.tel:
        # Получение информации по номеру телефона
        print(f"Searching by phone: {args.tel}") # Добавляем
        results = await telegram.search_entities(tel=args.tel)
        if results:
            print_entity_info(results[0])#Убрал telegram
        else:
            print("Entity not found.")

    elif args.id:
        # Получение информации по ID
        print(f"Searching by ID: {args.id}") # Добавляем
        results = await telegram.search_entities(id=args.id)
        if results:
            print_entity_info(results[0])#Убрал telegram
        else:
            print("Entity not found.")
    elif args.title:
        print(f"Searching by title: {args.title}") # Добавляем
        results = await telegram.search_entities(title=args.title)
        if results:
            print("Search Results:")
            for entity in results:
                print_entity_info(entity) #Убрал telegram, передаем список
                print("---")
        else:
            print("No entities found matching the search criteria.")

    elif args.recent_messages:
        # Получение последних сообщений
        print(f"Getting recent messages for: {args.recent_messages}, limit: {args.limit}")  # Добавляем
        try:  # Добавляем try...except
            messages = await telegram.get_recent_messages(args.recent_messages, limit=args.limit)
            if messages:
                print(f"Recent Messages (last {len(messages)}):")
                for message in messages:
                    print_message(message) #Одна строка
            else:
                print("Could not retrieve recent messages.")
        except Exception as e:
            print(f"An error occurred in main: {e}")  # Добавляем вывод ошибки

    else:
        #Если ничего не нашли
        print("Entity not found.")

    print("--- ENDING MAIN ---") # Добавляем


def print_entity_info(entity): #Убираем telegram
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

def print_message(message):
    """Выводит информацию о сообщении в одну строку."""
    # from_id = get_peer_id(message.sender) if message.sender else '(unknown)'
    if message.sender:
        if hasattr(message.sender, 'title'):  #Для каналов
            sender_info = message.sender.title
        elif hasattr(message.sender, 'username') and message.sender.username:
            sender_info = f"@{message.sender.username}"
        elif hasattr(message.sender, 'first_name'):
            sender_info = f"{message.sender.first_name} {message.sender.last_name if hasattr(message.sender, 'last_name') else ''}"
        else:
            sender_info = str(get_peer_id(message.sender)) #Если нет имени, выводим полный ID
    else:
        sender_info = "(unknown)"

    media_info = f" ({type(message.media).__name__})" if message.media else ""

    print(f"Message ID: {message.id}, Date: {message.date.isoformat()}, From: {sender_info}{media_info}: {message.text}")

if __name__ == "__main__":
    asyncio.run(main())
