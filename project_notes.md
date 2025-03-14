# Telegram GPT Assistant - Project Notes

## Цель проекта

Создание GPT-ассистента для анализа Telegram-чатов/групп.

## Целевая аудитория

*   **MVP:** AirVetra (разработчик и пользователь)
*   **Потенциальная:** Любой пользователь Telegram с потребностью в расширенной аналитике.

## MVP (Minimum Viable Product)

### Функциональность

1.  **Добавление источников:**
    *   Возможность добавлять Telegram-чаты, группы и каналы (для начала – один).
    *   Загрузка истории сообщений.
    *   Отслеживание новых сообщений (онлайн или с небольшой задержкой).

2.  **Обработка данных:**
    *   Загрузка: текст, эмодзи, ссылки, изображения.
    *   Приоритет (MVP): Анализ текста, эмодзи, ссылок.
    *   Перспектива: OCR (текст с изображений).

3.  **Интеграция LLM:**
    *   Подключение LLM (варианты см. ниже).
    *   Возможности LLM:
        *   Анализ и семантический поиск по темам.
        *   Ответы на вопросы по темам чата (с указанием участников и ссылками).
        *   Атрибуция участников по уровню доверия (со временем).
        *   Классификация участников (со временем).
        *   Генерация саммари.

4.  **Use Case:**
    *   Загрузка 2-3 чатов.
    *   Письменный запрос (пример про ВНЖ).
    *   Ответ системы: саммари, эксперты, ссылки.

## Технологический стек

*   **Python:** 3.12
*   **Telegram API:** Telethon
*   **LLM (варианты):**
    *   **Онлайн (через API):**
        *   Google Gemini API (предпочтительно)
        *   OpenAI API (если есть доступ и бюджет)
    *   **Локально:**
        *   Hugging Face Transformers + модель (выбор модели TBD)
        *   Ollama + модель (выбор модели TBD)
*   **NLP:** spaCy / NLTK / gensim (выбор по необходимости)
*   **Хранение данных:** SQLite (для начала)

## Настройка окружения

1.  **Установить Python 3.12** (если еще не установлен).
2.  **Создать репозиторий на GitHub:** `telegram-gpt-assistant`.
3.  **Создать виртуальное окружение:**
    ```bash
    python3.12 -m venv venv
    ```
4.  **Активировать виртуальное окружение:**
    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
5.  **Установить Telethon:**
    ```bash
    pip install telethon
    ```
6. **Установить python-dotenv**
    ```bash
        pip install python-dotenv
     ```

## Подключение к Telegram

1.  **Получить API ID и API Hash:**
    *   Зарегистрироваться на [my.telegram.org](https://my.telegram.org/).
    *   Создать приложение.
    *   Сохранить API ID и API Hash.

2.  **Создать файл `config.py`:**

    ```python
    # config.py
    API_ID =  # Ваш API ID (число)
    API_HASH = ''  # Ваш API Hash (строка)
    PHONE_NUMBER = '' # Ваш номер телефона
    ```

3.  **Добавить `config.py` в `.gitignore`:**

    *   Создать файл `.gitignore` (если его нет).
    *   Добавить в него строку:
        ```
        config.py
        ```

4.  **Создать файл `connect.py`:**

    ```python
    import os
    from telethon.sync import TelegramClient
    #from dotenv import load_dotenv #Раскоментировать, если используем .env
    import config

    #load_dotenv() # Раскоментировать, если используем .env

    #api_id = int(os.getenv('TELEGRAM_API_ID')) # Раскоментировать, если используем .env
    #api_hash = os.getenv('TELEGRAM_API_HASH')# Раскоментировать, если используем .env
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

    ```

5.  **Запустить `connect.py`:**
    ```bash
    python connect.py
    ```
    *   Ввести код подтверждения из Telegram.
    *   Убедиться, что скрипт выводит имя пользователя.

## LLM (варианты использования)

### 1. Онлайн (через API)

*   **Преимущества:** Простота использования, высокая производительность, не требует локальных ресурсов.
*   **Недостатки:** Зависимость от интернет-соединения, ограничения по количеству запросов (для бесплатных тарифов).
*   **Варианты:**
    *   **Google Gemini API:**
        *   Получить API-ключ на [ai.google.dev](https://ai.google.dev/).
    *   **OpenAI API:**
        *   Если есть доступ и бюджет.

### 2. Локально

*   **Преимущества:** Полный контроль над данными, независимость от интернет-соединения, возможность использовать бесплатные модели.
*   **Недостатки:** Требует вычислительных ресурсов (CPU/GPU), более сложная настройка.
*   **Варианты:**
    *   **Hugging Face Transformers:**
        *   Большой выбор моделей.
        *   Требует установки дополнительных библиотек (PyTorch/TensorFlow).
        *   Может потребоваться GPU для больших моделей.
    *   **Ollama:**
        *   Упрощает запуск и управление моделями.
        *   Поддерживает различные модели (Llama 2, Mistral и др.).
        *   Может работать как на CPU, так и на GPU.
    * **Выбор конкретной модели:** Будет зависеть от доступных ресурсов (CPU/GPU, объем памяти), требований к качеству и скорости работы.

## Дальнейшие шаги

*  Определиться с вариантом LLM (онлайн/локально). Если локально - выбрать модель.
*  Реализовать загрузку истории сообщений из Telegram-чата.
*  Реализовать отслеживание новых сообщений.

