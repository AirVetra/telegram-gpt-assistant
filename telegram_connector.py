from telethon.sync import TelegramClient
from telethon.errors import PeerIdInvalidError, FloodWaitError, ChatIdInvalidError
from aiolimiter import AsyncLimiter
import logging
import asyncio
import random
import telethon
from telethon.utils import get_peer_id
from telethon.tl.types import InputPhoneContact, Chat, Channel, User, ChatForbidden, ChannelForbidden, InputPeerChannel
from telethon.tl.functions.contacts import ImportContactsRequest, GetContactsRequest
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TelegramConnector:
    def __init__(self, api_id, api_hash, phone_number, session_name='my_session',
                 max_rate=20, time_period=1):  # Параметры для rate limiting
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self.limiter = AsyncLimiter(max_rate, time_period)  # Ограничитель запросов
        self.entity_cache = {}  # Кэш для информации о сущностях

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

    async def get_saved_messages(self, limit=100):
        async with self.limiter:
            me = await self.client.get_me()
        dialogs = await self.client.get_dialogs()
        saved_messages_dialog = None
        for dialog in dialogs:
            if dialog.is_user and dialog.entity.id == me.id:
                saved_messages_dialog = dialog
                break

        if saved_messages_dialog is None:
            logging.warning("Could not find Saved Messages dialog.")
            return []

        messages = []
        async for message in self.client.iter_messages(saved_messages_dialog, limit=limit): #Используем итератор
            async with self.limiter:  # rate limit inside the loop
                messages.append(message)
            await asyncio.sleep(random.uniform(1, 3)) #Дополнительная пауза
        return messages


    async def get_entity_info(self, entity_identifier):
        #УДАЛЯЕМ, так как используем search_entities
        pass

    def get_entity_type(self, entity):
        if isinstance(entity, telethon.types.Chat):
            return "Chat"
        elif isinstance(entity, telethon.types.Channel):
            return "Channel"
        elif isinstance(entity, telethon.types.User):
            return "User"
        elif isinstance(entity, telethon.types.ChatForbidden):
            return "ChatForbidden"
        elif isinstance(entity, telethon.types.ChannelForbidden):
            return "ChannelForbidden"
        else:
            return "Unknown"

    async def search_contacts_by_name(self, first_name=None, last_name=None):
        #УДАЛЯЕМ, так как используем search_entities
        pass

    async def export_dialogs_to_csv(self, filename="dialogs.csv"):
        """Экспортирует информацию о диалогах пользователя в CSV-файл."""

        if not self.client.is_connected(): #Проверяем, подключены ли мы
            await self.connect()

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'full_id', 'id', 'title', 'username', 'type',
                'is_user', 'is_group', 'is_channel',
                'date', 'unread_count',
                'first_name', 'last_name', 'phone',
                'participants_count', 'admins_count', 'kicked_count', 'banned_count',
                'about', 'access_hash' #добавляем access_hash
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            async for dialog in self.client.iter_dialogs(): # Используем iter_dialogs()
                async with self.limiter: # И limiter внутри цикла
                    entity = dialog.entity
                    row = {
                        'full_id': get_peer_id(entity),
                        'id': entity.id,
                        'title': getattr(entity, 'title', None),
                        'username': getattr(entity, 'username', None),
                        'type': self.get_entity_type(entity),
                        'is_user': dialog.is_user,
                        'is_group': dialog.is_group,
                        'is_channel': dialog.is_channel,
                        'date': dialog.date.isoformat() if dialog.date else None,
                        'unread_count': dialog.unread_count,
                        'access_hash': getattr(entity, 'access_hash', None) #Добавляем access_hash

                    }
                    # Добавляем специфичные для разных типов
                    if dialog.is_user:
                        row.update({
                            'first_name': getattr(entity, 'first_name', None),
                            'last_name': getattr(entity, 'last_name', None),
                            'phone': getattr(entity, 'phone', None),
                            'about': getattr(entity, 'about', None),
                        })
                    if dialog.is_group:
                        row.update({
                            'participants_count': getattr(entity, 'participants_count', None),
                            'admins_count': getattr(entity, 'admins_count', None),
                            'kicked_count': getattr(entity, 'kicked_count', None),
                            'banned_count': getattr(entity, 'banned_count', None),
                            'about': getattr(entity, 'about', None),
                        })
                    if dialog.is_channel:
                        row.update({
                            'participants_count': getattr(entity, 'participants_count', None),  # Канал - это супергруппа
                            'about': getattr(entity, 'about', None),
                        })

                    writer.writerow(row)
        logging.info(f"Dialogs exported to {filename}")

    async def search_dialogs_by_title(self, title):
        #УДАЛЯЕМ, так как используем search_entities
        pass

    async def search_entities(self, id=None, user=None, tel=None, first_name=None, last_name=None, title=None):
        """Ищет сущности (пользователей, чаты, каналы) по различным критериям."""

        results = []

        if id:
            # Поиск по ID
            async with self.limiter:
                try:
                    entity_id = int(id)  # Приводим ID к числу
                except ValueError:
                    logging.error(f"Invalid ID format: {id}. ID must be an integer.")
                    return []

                try:
                    #Пытаемся получить entity по ID
                    entity = await self.client.get_entity(get_peer_id(entity_id))
                    entity.full_id = get_peer_id(entity) #Добавляем атрибут
                    results.append(entity)

                except ChatIdInvalidError:
                    logging.error(f"Could not find entity with ID {id} (invalid chat ID).")
                    return []
                except PeerIdInvalidError:
                    logging.info(f"Entity with id {id} not found.")
                    return []  # Возвращаем пустой список, если не нашли
                except ValueError as e:
                    logging.error(f"Error getting entity by ID {id}: {e}") #Другая ошибка
                    return []
                except FloodWaitError as e:
                    logging.error(f"Flood wait required: {e.seconds} seconds.")
                    return [] #Прекращаем в случае Flood
                except TypeError as e:
                    logging.error(f"Type Error: {e}")
                    return []


        elif user:
            # Поиск по username
            try:
                async with self.limiter:
                    entity = await self.client.get_entity(user)
                    entity.full_id = get_peer_id(entity)  # Добавляем атрибут full_id
                if entity:
                    results.append(entity)
            except (PeerIdInvalidError, ValueError):
                logging.info(f"Entity with username {user} not found.")
            except FloodWaitError as e:
                logging.error(f"Flood wait required: {e.seconds} seconds.")
                return []

        elif tel:
            # Поиск по номеру телефона
            try:
                async with self.limiter:
                    # Сначала проверяем, есть ли контакт с таким номером в адресной книге
                    contacts = await self.client(GetContactsRequest(hash=0))
                    found_user = None
                    for user in contacts.users:
                        if user.phone == tel.lstrip('+'):
                            found_user = user
                            break

                    if found_user:
                        found_user.full_id = get_peer_id(found_user) #Добавляем
                        results.append(found_user)
                        logging.info(f"Found user with phone {tel} in contacts.")
                    else:
                        # Если контакт не найден, импортируем его
                        logging.info(f"Importing contact with phone {tel}...")
                        try:
                            contact = InputPhoneContact(client_id=0, phone=tel, first_name='Temp', last_name='')
                            result = await self.client(ImportContactsRequest([contact]))
                            # Получаем пользователя из импортированных контактов
                            if result.users:
                                entity = result.users[0]
                                entity.full_id = get_peer_id(entity)  # Добавляем атрибут full_id
                                results.append(entity)
                            else:
                                raise ValueError(f"Could not import contact for phone number: {tel}")
                        except Exception as e:
                            logging.error(f"Error importing contact or getting entity by phone: {e}")
                            return []
            except FloodWaitError as e:
                logging.error(f"Flood wait required: {e.seconds} seconds.")
                return []


        elif first_name or last_name:
            # Поиск по имени и/или фамилии (среди контактов)
            async with self.limiter:
                contacts = await self.client(GetContactsRequest(hash=0))
            await asyncio.sleep(2)

            for user in contacts.users:
                match = True
                if first_name:
                    if not hasattr(user, 'first_name') or user.first_name is None or first_name.lower() not in user.first_name.lower():
                        match = False
                if match and last_name:
                    if not hasattr(user, 'last_name') or user.last_name is None or last_name.lower() not in user.last_name.lower():
                        match = False
                if match:
                    user.full_id = get_peer_id(user) #Добавляем
                    results.append(user)

        elif title:
            # Поиск по названию (среди диалогов)
            async for dialog in self.client.iter_dialogs():
                async with self.limiter:
                    if hasattr(dialog.entity, 'title') and dialog.entity.title and title.lower() in dialog.entity.title.lower():
                        dialog.entity.full_id = get_peer_id(dialog.entity) #Добавляем
                        results.append(dialog.entity) #Сохраняем именно entity

        return results
