import pytest
import asyncio
import argparse
from unittest.mock import AsyncMock, patch, MagicMock
import config  # Твой файл config.py
from telegram_connector import TelegramConnector
from main import main, print_entity_info  # Импортируем main и print_entity_info
from telethon.errors import PeerIdInvalidError, FloodWaitError, ChatIdInvalidError

# Создаем фикстуру (fixture) для TelegramConnector, чтобы не подключаться к Telegram при каждом тесте
@pytest.fixture
async def mock_telegram_connector():
    # Создаем мок-объект TelegramConnector
    mock_connector = AsyncMock(spec=TelegramConnector)

    # Настраиваем поведение мок-объекта
    mock_connector.connect = AsyncMock()  # connect() ничего не делает

    # Возвращаем мок-объект
    yield mock_connector

@pytest.fixture(autouse=True) #Чтобы patch применялся ко всем тестам
def patch_connector(mock_telegram_connector):
    with patch('main.TelegramConnector', return_value=mock_telegram_connector):
        yield

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_id, expected_type, expected_title, expected_username",
    [
        ("-1001682024103", "Channel", "Test Channel", None),  # Канал
        ("123456789", "User", None, "testuser"),  # Пользователь
        ("-123456789", "Chat", "Test Chat", None),  # Чат (группа)
    ],
)
async def test_search_by_valid_id(mock_telegram_connector, capsys, entity_id, expected_type, expected_title, expected_username):
    # Настраиваем возвращаемое значение для get_entity_info (валидный ID)
    mock_entity = AsyncMock()
    mock_entity.id = int(entity_id) #Приводим к int
    mock_entity.title = expected_title
    mock_entity.username = expected_username
    mock_telegram_connector.search_entities.return_value = [mock_entity]
    mock_telegram_connector.get_entity_type.return_value = expected_type

    # Запускаем main с аргументом --id
    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(id=entity_id, user=None, tel=None, first_name=None, last_name=None, title=None)):
        await main()

    # Проверяем вывод
    captured = capsys.readouterr()
    assert "Entity Information:" in captured.out
    assert f"ID: {entity_id}" in captured.out
    if expected_title:
        assert f"Title: {expected_title}" in captured.out
    if expected_username:
        assert f"Username: {expected_username}" in captured.out
    assert f"Type: {expected_type}" in captured.out


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

    mock_telegram_connector.search_entities.return_value = [] #Ничего не возвращаем

    # Запускаем main
    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(id=entity_id, user=None, tel=None, first_name=None, last_name=None, title=None)):
        await main()

    captured = capsys.readouterr()
    assert "No entities found" in captured.out


@pytest.mark.asyncio
async def test_search_by_existing_title(mock_telegram_connector, capsys):
    # Настраиваем search_dialogs_by_title
    mock_dialog = AsyncMock()
    mock_dialog.entity.id = -1001123456789
    mock_dialog.entity.title = "Emprendedores"
    mock_dialog.entity.username = "emprendedores_chat"
    mock_telegram_connector.search_entities.return_value = [mock_dialog.entity]
    mock_telegram_connector.get_entity_type.return_value = "Channel"  # Допустим, это канал

    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(title='Emprendedores', user=None, tel=None, id=None, first_name=None, last_name=None)):
        await main()

    captured = capsys.readouterr()
    assert "Search Results:" in captured.out
    assert "ID: -1001123456789" in captured.out
    assert "Title: Emprendedores" in captured.out
    assert "Username: emprendedores_chat" in captured.out
    assert "Type: Channel" in captured.out


@pytest.mark.asyncio
async def test_search_by_nonexistent_title(mock_telegram_connector, capsys):
    mock_telegram_connector.search_entities.return_value = []  # Ничего не найдено
    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(title='NonExistentTitle', user=None, tel=None, id=None, first_name=None, last_name=None)):
        await main()

    captured = capsys.readouterr()
    assert "No entities found" in captured.out



@pytest.mark.asyncio
async def test_search_by_first_name(mock_telegram_connector, capsys):
    # Настраиваем search_contacts_by_name
    mock_user = AsyncMock()
    mock_user.id = 123456789
    mock_user.first_name = "Кристина"
    mock_user.last_name = "Иванова"
    mock_user.username = "kristina_ivanova"
    mock_user.phone = "+79991234567"
    mock_telegram_connector.search_entities.return_value = [mock_user]
    mock_telegram_connector.get_entity_type.return_value = "User"

    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(first_name='Кристина', last_name=None, user=None, tel=None, id=None, title=None)):
        await main()

    captured = capsys.readouterr()
    assert "Search Results:" in captured.out
    assert "ID: 123456789" in captured.out
    assert "First Name: Кристина" in captured.out
    assert "Last Name: Иванова" in captured.out
    assert "Username: kristina_ivanova" in captured.out
    assert "Phone: +79991234567" in captured.out
    assert "Type: User" in captured.out


@pytest.mark.asyncio
async def test_search_by_last_name(mock_telegram_connector, capsys):
    mock_user = AsyncMock()
    mock_user.id = 987654321
    mock_user.first_name = "Петр"
    mock_user.last_name = "Рупша"
    mock_user.username = None
    mock_user.phone = "+79999999999"
    mock_telegram_connector.search_entities.return_value = [mock_user]
    mock_telegram_connector.get_entity_type.return_value = "User"
    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(first_name=None, last_name="Рупша", user=None, tel=None, id=None, title=None)):
        await main()
    captured = capsys.readouterr()
    assert "Search Results:" in captured.out
    assert "ID: 987654321" in captured.out
    assert "First Name: Петр" in captured.out
    assert "Last Name: Рупша" in captured.out
    assert "Phone: +79999999999" in captured.out
    assert "Type: User" in captured.out

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "phone",
    [
        ("+79118668098"),
        ("79118668098"),
    ],
)
async def test_search_by_tel(mock_telegram_connector, capsys, phone):
    # Настраиваем get_entity_info для телефона
    mock_user = AsyncMock()
    mock_user.id = 469360577
    mock_user.first_name = "Кристина"
    mock_user.last_name = "Рупшайте"
    mock_user.username = "kristina_rupshayte"
    mock_user.phone = "79118668098"  # Используем отформатированный номер
    mock_telegram_connector.search_entities.return_value = [mock_user]
    mock_telegram_connector.get_entity_type.return_value = "User"
    # Запускаем main с аргументом --tel

    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(tel=phone, user=None, id=None, first_name=None, last_name=None, title=None)):
        await main()

    # Проверяем вывод
    captured = capsys.readouterr()
    assert "Entity Information:" in captured.out
    assert "ID: 469360577" in captured.out
    assert "First Name: Кристина" in captured.out
    assert "Last Name: Рупшайте" in captured.out
    assert "Username: kristina_rupshayte" in captured.out
    assert "Phone: 79118668098" in captured.out
    assert "Type: User" in captured.out

@pytest.mark.asyncio
async def test_search_by_nonexistent_tel(mock_telegram_connector, capsys):
    mock_telegram_connector.search_entities.return_value = []
    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(tel='+70000000000', user=None, id=None, first_name=None, last_name=None, title=None)):
        await main()
    captured = capsys.readouterr()
    assert "No entities found" in captured.out

@pytest.mark.asyncio
async def test_search_by_nonexistent_username(mock_telegram_connector, capsys):
    mock_telegram_connector.search_entities.return_value = []
    with patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(user='NonExistentUser', tel=None, id=None, first_name=None, last_name=None, title=None)):
        await main()
    captured = capsys.readouterr()
    assert "No entities found" in captured.out


@pytest.mark.asyncio
async def test_flood_wait_error(mock_telegram_connector, capsys):

    # Настраиваем search_entities, чтобы он возвращал FloodWaitError
    mock_telegram_connector.search_entities.side_effect = FloodWaitError(request=None, seconds=10)

    with patch('argparse.ArgumentParser.parse_args',
            return_value=argparse.Namespace(user='someuser', tel=None, id=None, first_name=None, last_name=None, title=None)):
        await main()

    captured = capsys.readouterr()
    assert "No entities found" in captured.out #Так как search entities возвращает []

