import asyncio
import argparse
import config
from telegram_connector import TelegramConnector


async def main():
    # Настраиваем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Get information about a Telegram entity or search contacts by name.")
    group = parser.add_mutually_exclusive_group(required=True)  # Добавляем взаимоисключающую группу
    group.add_argument("--user", help="Username of the Telegram entity")
    group.add_argument("--tel", help="Phone number of the Telegram entity")
    group.add_argument("--id", help="ID of the Telegram entity")
    group.add_argument("--first_name", help="First name for searching contacts") #Добавляем в группу
    group.add_argument("--last_name", help="Last name for searching contacts") #Добавляем в группу

    args = parser.parse_args()

    telegram = TelegramConnector(config.API_ID, config.API_HASH, config.PHONE_NUMBER)
    await telegram.connect()

    if args.first_name or args.last_name:
        # Поиск по имени/фамилии
        results = await telegram.search_contacts_by_name(first_name=args.first_name, last_name=args.last_name)
        if results:
            print("Search Results:")
            for user in results:
                print(f"  ID: {user.id}")
                if hasattr(user, 'first_name'):
                    print(f"  First Name: {user.first_name}")
                if hasattr(user, 'last_name'):
                    print(f"  Last Name: {user.last_name}")
                if hasattr(user, 'username'):
                    print(f"  Username: {user.username}")
                if hasattr(user, 'phone'):
                    print(f"  Phone: {user.phone}")
                print(f"  Type: {telegram.get_entity_type(user)}")
                print("---")
        else:
            print("No contacts found matching the search criteria.")

    elif args.user:
        # Получение информации по username
        entity = await telegram.get_entity_info(args.user)
        print_entity_info(entity, telegram) #Выносим в отдельную функцию

    elif args.tel:
        # Получение информации по номеру телефона
        entity = await telegram.get_entity_info(args.tel)
        print_entity_info(entity, telegram) #Выносим в отдельную функцию

    elif args.id:
        # Получение информации по ID
        entity = await telegram.get_entity_info(args.id)
        print_entity_info(entity, telegram) #Выносим в отдельную функцию
    else:
       #Если ничего не нашли
        print("Entity not found.")

def print_entity_info(entity, telegram): #Функция вывода
    if entity:
        print("Entity Information:")
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

    else:
        print("Entity not found.")

if __name__ == "__main__":
    asyncio.run(main())
