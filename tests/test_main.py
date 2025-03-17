import pytest
import asyncio
import argparse
from unittest.mock import AsyncMock, patch
import config  # Твой файл config.py
from telegram_connector import TelegramConnector
from main import main, print_entity_info  # Импортируем main и print_entity_info
from telethon.errors import PeerIdInvalidError, FloodWaitError, ChatIdInvalidError
from telethon.utils import get_peer_id
import pytest_asyncio


@pytest_asyncio.fixture
async def mock_telegram_connector():
    mock_connector = AsyncMock(spec=TelegramConnector)
    mock_connector.connect = AsyncMock()
    return mock_connector


@pytest.mark.asyncio
async def test_search_by_username_existing(mock_telegram_connector, capsys):
    """
    Тест поиска по существующему username.
    Ожидается, что будет найден один пользователь.
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_user = AsyncMock()
        mock_user.id = 123456789
        mock_user.full_id = 123456789
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.username = "testuser"
        mock_user.phone = "+1234567890"
        mock_user.access_hash = 12345
        mock_user.type = "User"  # Добавляем тип
        mock_telegram_connector.search_entities.return_value = [mock_user]
        #mock_telegram_connector.get_entity_type.return_value = "User" #Убираем

        # 2. Выполнение действия (запуск main с аргументом --user)
        with patch('argparse.ArgumentParser.parse_args',
                   return_value=argparse.Namespace(user="testuser", tel=None, id=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert "Search Results:" in captured.out
        assert any("Full ID: 123456789" in line for line in lines)
        assert any("ID: 123456789" in line for line in lines)
        assert any("First Name: Test" in line for line in lines)
        assert any("Last Name: User" in line for line in lines)
        assert any("Username: testuser" in line for line in lines)
        assert any("Phone: +1234567890" in line for line in lines)
        assert any("Type: User" in line for line in lines)
        assert any("---" in line for line in lines)


@pytest.mark.asyncio
async def test_search_by_username_not_found(mock_telegram_connector, capsys):
    """
    Тест поиска по несуществующему username.
    Ожидается, что ничего не будет найдено.
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_telegram_connector.search_entities.return_value = []  # Ничего не найдено

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                   return_value=argparse.Namespace(user="nonexistentuser", tel=None, id=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        assert "No entities found" in captured.out


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_id, expected_full_id, expected_type, expected_title, expected_username",
    [
        ("-1001682024103", -1001682024103, "Channel", "Test Channel", None),  # Канал (существующий)
        ("123456789", 123456789, "User", None, "testuser"),  # Пользователь
        ("-123456789", -123456789, "Chat", "Test Chat", None),  # Чат (группа)
    ],
)
async def test_search_by_valid_id(mock_telegram_connector, capsys, entity_id, expected_full_id, expected_type, expected_title, expected_username):
    """
    Тест поиска по существующему ID (канал, пользователь, чат).
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):

        # 1. Подготовка данных
        mock_entity = AsyncMock()
        mock_entity.id = int(entity_id)  # Приводим к int, т.к. ID - число
        mock_entity.full_id = expected_full_id #Добавляем full_id
        mock_entity.title = expected_title
        mock_entity.username = expected_username
        mock_entity.access_hash = 456 #Добавляем access_hash
        mock_entity.type = expected_type #Добавляем
        mock_telegram_connector.search_entities.return_value = [mock_entity]
        #mock_telegram_connector.get_entity_type.return_value = expected_type #Убираем

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                   return_value=argparse.Namespace(id=entity_id, user=None, tel=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert "Search Results:" in captured.out
        assert any(f"Full ID: {expected_full_id}" in line for line in lines)
        assert any(f"ID: {entity_id}" in line for line in lines)
        if expected_title:
            assert any(f"Title: {expected_title}" in line for line in lines)
        if expected_username:
            assert any(f"Username: {expected_username}" in line for line in lines)
        assert any(f"Type: {expected_type}" in line for line in lines)
        assert any("---" in line for line in lines)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_id",
    [
        ("-999999999999"),  # Несуществующий канал
        ("9999999999"),  # Несуществующий пользователь
        ("-9999999999"),  # Несуществующий чат
    ],
)
async def test_search_by_invalid_id(mock_telegram_connector, capsys, entity_id):
    """
    Тест поиска по несуществующему ID (канал, пользователь, чат).
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_telegram_connector.search_entities.return_value = []

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                    return_value=argparse.Namespace(id=entity_id, user=None, tel=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        assert "No entities found" in captured.out


@pytest.mark.asyncio
async def test_search_by_existing_title(mock_telegram_connector, capsys):
    """
    Тест поиска по существующему названию диалога.
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_dialog = AsyncMock()
        mock_dialog.entity.id = -1001123456789
        mock_dialog.entity.full_id = -1001123456789 #Добавляем
        mock_dialog.entity.title = "Emprendedores"
        mock_dialog.entity.username = "emprendedores_chat"
        mock_dialog.entity.access_hash = 789 #Добавляем
        mock_dialog.entity.type = "Channel"
        mock_telegram_connector.search_entities.return_value = [mock_dialog.entity]
        #mock_telegram_connector.get_entity_type.return_value = "Channel"  # Допустим, это канал #Убираем

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                   return_value=argparse.Namespace(title='Emprendedores', user=None, tel=None, id=None, first_name=None, last_name=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert "Search Results:" in captured.out
        assert any(f"Full ID: -1001123456789" in line for line in lines)
        assert any("ID: -1001123456789" in line for line in lines)
        assert any("Title: Emprendedores" in line for line in lines)
        assert any("Username: emprendedores_chat" in line for line in lines)
        assert any("Type: Channel" in line for line in lines)
        assert any("---" in line for line in lines)


@pytest.mark.asyncio
async def test_search_by_nonexistent_title(mock_telegram_connector, capsys):
    """
    Тест поиска по несуществующему названию диалога.
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_telegram_connector.search_entities.return_value = []

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                    return_value=argparse.Namespace(title='NonExistentTitle', user=None, tel=None, id=None, first_name=None, last_name=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        assert "No entities found" in captured.out


@pytest.mark.asyncio
async def test_search_by_first_name(mock_telegram_connector, capsys):
    """
    Тест поиска по имени пользователя (среди контактов).
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_user = AsyncMock()
        mock_user.id = 123456789
        mock_user.full_id = 123456789 #Добавляем
        mock_user.first_name = "Кристина"
        mock_user.last_name = "Иванова"
        mock_user.username = "kristina_ivanova"
        mock_user.phone = "+79991234567"
        mock_user.access_hash = 147 #Добавляем
        mock_user.type = "User" #Добавляем
        mock_telegram_connector.search_entities.return_value = [mock_user]
        #mock_telegram_connector.get_entity_type.return_value = "User" #Убираем

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                   return_value=argparse.Namespace(first_name='Кристина', last_name=None, user=None, tel=None, id=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        lines = captured.out.splitlines()
        assert "Search Results:" in captured.out
        assert any(f"Full ID: {mock_user.full_id}" in line for line in lines)
        assert any("ID: 123456789" in line for line in lines)
        assert any("First Name: Кристина" in line for line in lines)
        assert any("Last Name: Иванова" in line for line in lines)
        assert any("Username: kristina_ivanova" in line for line in lines)
        assert any("Phone: +79991234567" in line for line in lines)
        assert any("Type: User" in line for line in lines)
        assert any("---" in line for line in lines)



@pytest.mark.asyncio
async def test_search_by_last_name(mock_telegram_connector, capsys):
    """
    Тест поиска по фамилии пользователя (среди контактов).
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):

        # 1. Подготовка данных
        mock_user = AsyncMock()
        mock_user.id = 987654321
        mock_user.full_id = 987654321
        mock_user.first_name = "Петр"
        mock_user.last_name = "Рупша"
        mock_user.username = None
        mock_user.phone = "+79999999999"
        mock_user.access_hash = 258
        mock_user.type = "User" #Добавляем
        mock_telegram_connector.search_entities.return_value = [mock_user]
        #mock_telegram_connector.get_entity_type.return_value = "User" #Убираем

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                    return_value=argparse.Namespace(first_name=None, last_name="Рупша", user=None, tel=None, id=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert "Search Results:" in captured.out
        assert any(f"Full ID: {mock_user.full_id}" in line for line in lines)
        assert any("ID: 987654321" in line for line in lines)
        assert any("First Name: Петр" in line for line in lines)
        assert any("Last Name: Рупша" in line for line in lines)
        assert any("Phone: +79999999999" in line for line in lines)
        assert any("Type: User" in line for line in lines)
        assert any("---" in line for line in lines)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "phone",
    [
        ("+79118668098"),
        ("79118668098"),
    ],
)
async def test_search_by_tel(mock_telegram_connector, capsys, phone):
    """
    Тест поиска по номеру телефона (с "+" и без "+").
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_user = AsyncMock()
        mock_user.id = 469360577
        mock_user.full_id = 469360577
        mock_user.first_name = "Кристина"
        mock_user.last_name = "Рупшайте"
        mock_user.username = "kristina_rupshayte"
        mock_user.phone = "79118668098"  # Используем отформатированный номер
        mock_user.access_hash = 369
        mock_user.type = "User"
        mock_telegram_connector.search_entities.return_value = [mock_user]
        #mock_telegram_connector.get_entity_type.return_value = "User" #Убираем

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                   return_value=argparse.Namespace(tel=phone, user=None, id=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert "Search Results:" in captured.out
        assert any(f"Full ID: {mock_user.full_id}" in line for line in lines)
        assert any("ID: 469360577" in line for line in lines)
        assert any("First Name: Кристина" in line for line in lines)
        assert any("Last Name: Рупшайте" in line for line in lines)
        assert any("Username: kristina_rupshayte" in line for line in lines)
        assert any("Phone: 79118668098" in line for line in lines)
        assert any("Type: User" in line for line in lines)
        assert any("---" in line for line in lines)

@pytest.mark.asyncio
async def test_search_by_nonexistent_tel(mock_telegram_connector, capsys):
    """
    Тест поиска по несуществующему номеру телефона.
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):

        # 1. Подготовка данных
        mock_telegram_connector.search_entities.return_value = []

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                    return_value=argparse.Namespace(tel='+70000000000', user=None, id=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        assert "No entities found" in captured.out

@pytest.mark.asyncio
async def test_search_by_nonexistent_username(mock_telegram_connector, capsys):
    """
    Тест поиска по несуществующему username.
    """
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        # 1. Подготовка данных
        mock_telegram_connector.search_entities.return_value = []

        # 2. Выполнение действия
        with patch('argparse.ArgumentParser.parse_args',
                    return_value=argparse.Namespace(user='NonExistentUser', tel=None, id=None, first_name=None, last_name=None, title=None)):
            await main()

        # 3. Проверки
        captured = capsys.readouterr()
        assert "No entities found" in captured.out
