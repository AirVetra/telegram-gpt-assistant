from telethon.sync import TelegramClient
from telethon.errors import PeerIdInvalidError, FloodWaitError
from aiolimiter import AsyncLimiter
import logging
import asyncio
import random
import telethon
from telethon.utils import get_peer_id
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest, GetContactsRequest

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
        logging.info(f"Getting info for entity: {entity_identifier}")

        if entity_identifier in self.entity_cache:
            logging.info("Getting entity info from cache...")
            return self.entity_cache[entity_identifier]

        try:
            async with self.limiter:  # Ограничиваем запросы
                #Определяем тип
                if entity_identifier.startswith('+'): #Если начинается с +, то это номер
                    # Сначала проверяем, есть ли контакт с таким номером в адресной книге
                    contacts = await self.client(GetContactsRequest(hash=0))
                    found_user = None
                    for user in contacts.users:
                        if user.phone == entity_identifier.lstrip('+'):  # Убираем +, на всякий случай
                            found_user = user
                            break

                    if found_user:
                        # Если контакт найден, используем его
                        entity = found_user
                        logging.info(f"Found user with phone {entity_identifier} in contacts.")
                    else:
                        # Если контакт не найден, импортируем его
                        logging.info(f"Importing contact with phone {entity_identifier}...")
                        try:
                            contact = InputPhoneContact(client_id=0, phone=entity_identifier, first_name='Temp', last_name='')
                            result = await self.client(ImportContactsRequest([contact]))

                            # Получаем пользователя из импортированных контактов
                            if result.users:
                                entity = result.users[0]
                            else:
                                raise ValueError(f"Could not import contact for phone number: {entity_identifier}")
                        except Exception as e:
                            logging.error(f"Error importing contact or getting entity by phone: {e}")
                            return None
                else: #Иначе - username или ID
                    try:
                        entity = await self.client.get_entity(entity_identifier)
                    except ValueError:
                        entity = await self.client.get_entity(get_peer_id(int(entity_identifier)))

            self.entity_cache[entity_identifier] = entity  # Сохраняем в кэш
            return entity

        except PeerIdInvalidError:
            logging.error(f"Could not find entity with identifier '{entity_identifier}'.")
            return None
        except FloodWaitError as e:
            logging.error(f"Flood wait required. Please wait {e.seconds} seconds.")
            return None
        except Exception as e:
            logging.exception("An unexpected error occurred")
            return None

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
        """Ищет пользователей в контактах по имени и/или фамилии."""

        results = []
        async with self.limiter: # Добавляем ограничитель скорости
            contacts = await self.client(GetContactsRequest(hash=0))
        await asyncio.sleep(2)  # Увеличиваем задержку до 2 секунд

        for user in contacts.users:
            match = True

            # Проверяем first_name
            if first_name:
                if not hasattr(user, 'first_name') or user.first_name is None or first_name.lower() not in user.first_name.lower():
                    match = False

            # Проверяем last_name, если совпало по first_name (или если first_name не указано)
            if match and last_name:
                if not hasattr(user, 'last_name') or user.last_name is None or last_name.lower() not in user.last_name.lower():
                    match = False

            if match:
                results.append(user)

        return results
