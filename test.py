import asyncio
import config
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChat, InputPeerChannel, InputPeerUser
from datetime import datetime

async def get_last_message(api_id, api_hash, phone_number, chat_identifier):
    """
    Получает последнее сообщение из указанного чата.

    Args:
        api_id: Telegram API ID.
        api_hash: Telegram API Hash.
        phone_number: Номер телефона.
        chat_identifier: ID чата (int) или username (str).

    Returns:
        Словарь с информацией о последнем сообщении или None, если произошла ошибка.
    """
    client = TelegramClient('last_message_session', api_id, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():  # Проверяем, авторизован ли клиент
            await client.send_code_request(phone_number)
            await client.sign_in(phone_number, input('Enter the code: '))

        me = await client.get_me()
        entity = await client.get_input_entity(chat_identifier)

        if entity:
            messages = await client.get_messages(entity, limit=1)  # Получаем только 1 сообщение
            if messages:
                message = messages[0]

                if message.sender_id == me.id:
                    sender_name = f"{me.first_name} {me.last_name or ''}".strip() if me.first_name else me.username or "Unknown"
                else:
                    sender = message.sender
                    sender_name = f"{sender.first_name} {sender.last_name or ''}".strip() if sender and sender.first_name else (sender.username if sender else "Unknown")

                formatted_date = message.date.strftime("%Y-%m-%d %H:%M:%S")

                return {
                    'id': message.id,
                    'sender': sender_name,
                    'date': formatted_date,
                    'text': message.text,
                }
            else:
                print(f"No messages found in chat: {chat_identifier}")
                return None
        else:
            print(f"Could not find entity for: {chat_identifier}")
            return None


    except ValueError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    finally:
        await client.disconnect()

async def main():
    # Используем данные из config.py
    chat_id = -4587777530  # ВСТАВЬ СЮДА ID ЧАТА
    last_message = await get_last_message(config.API_ID, config.API_HASH, config.PHONE_NUMBER, chat_id)

    if last_message:
        print(f"Last Message in chat {chat_id}:")
        print(f"  ID: {last_message['id']}, Author: {last_message['sender']}, Date: {last_message['date']}, Text: {last_message['text']}")
    else:
        print("Failed to retrieve the last message.")

if __name__ == "__main__":
    asyncio.run(main())
