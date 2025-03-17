import asyncio
import config
from telegram_connector import TelegramConnector

async def main():
    telegram = TelegramConnector(config.API_ID, config.API_HASH, config.PHONE_NUMBER)
    await telegram.connect()
    await telegram.export_dialogs_to_csv()

if __name__ == "__main__":
    asyncio.run(main())
