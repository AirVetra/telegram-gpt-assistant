from telethon.sync import TelegramClient
import config  # Импортируем config.py

api_id = config.API_ID
api_hash = config.API_HASH
phone_number = config.PHONE_NUMBER

client = TelegramClient('my_session', api_id, api_hash)

async def main():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        await client.sign_in(phone_number, input('Enter the code: '))

    me = await client.get_me()
    print(f"Successfully connected as {me.first_name} ({me.username}).")

with client:
    client.loop.run_until_complete(main())
