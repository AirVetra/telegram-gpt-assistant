import pytest
from unittest.mock import AsyncMock
from telethon.errors import FloodWaitError
from telegram_connector import TelegramConnector

@pytest.mark.asyncio
async def test_flood_wait_error_handling():
    """
    Тест обработки FloodWaitError в search_entities.
    """
    # Создаем мок-объект TelegramClient
    mock_client = AsyncMock()
    # Имитируем FloodWaitError при вызове search_entities
    mock_client.get_entity.side_effect = FloodWaitError(AsyncMock(), 10)

    # Создаем экземпляр TelegramConnector с мок-объектом клиента
    connector = TelegramConnector(api_id=123, api_hash='test_hash', phone_number='+11111')
    connector.client = mock_client  # Подменяем client на мок

    # Вызываем search_entities (ожидаем FloodWaitError и пустой результат)
    result = await connector.search_entities(user='someuser')

    # Проверяем, что результат пустой
    assert result == []

