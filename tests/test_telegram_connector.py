import pytest
from unittest.mock import AsyncMock, patch
from telethon.errors import FloodWaitError, PeerIdInvalidError, ChatIdInvalidError
from telegram_connector import TelegramConnector  # Твой TelegramConnector

# Модульные тесты для TelegramConnector

@pytest.mark.asyncio
async def test_flood_wait_error_handling():
    """
    Тест обработки FloodWaitError в search_entities.
    """
    # Создаем мок-объект TelegramClient
    mock_client = AsyncMock()
    # Имитируем FloodWaitError при вызове get_entity
    mock_client.get_entity.side_effect = FloodWaitError(AsyncMock(), 10) # seconds - позиционный

    # Создаем экземпляр TelegramConnector с мок-объектом клиента
    connector = TelegramConnector(api_id=123, api_hash='test_hash', phone_number='+11111') #Исправляем
    connector.client = mock_client  # Подменяем client на мок

    # Вызываем search_entities (ожидаем FloodWaitError и пустой результат)
    result = await connector.search_entities(id='123')

    # Проверяем, что результат пустой
    assert result == []

@pytest.mark.asyncio
async def test_peer_id_invalid_error_handling():
    """
    Тест на PeerIdInvalidError
    """
    mock_client = AsyncMock()
    mock_client.get_entity.side_effect = PeerIdInvalidError("SomePeer")
    connector = TelegramConnector(api_id=123, api_hash='test_hash', phone_number='+11111') #Исправляем
    connector.client = mock_client
    result = await connector.search_entities(id='invalid_id')
    assert result == []

@pytest.mark.asyncio
async def test_chat_id_invalid_error_handling():
    """
    Тест на ChatIdInvalidError
    """
    mock_client = AsyncMock()
    mock_client.get_entity.side_effect = ChatIdInvalidError("SomeChat")
    connector = TelegramConnector(api_id=123, api_hash='test_hash', phone_number='+11111') #Исправляем
    connector.client = mock_client
    result = await connector.search_entities(id='-100123')  # Передаем некорректный ID
    assert result == []
