import json
import pandas as pd
from pathlib import Path
import os

print(f"Current working directory: {os.getcwd()}")

def load_telegram_export(json_file_path):
    """
    Загружает данные из JSON-файла экспорта Telegram в pandas DataFrame.

    Args:
        json_file_path (str or Path): Путь к файлу result.json.

    Returns:
        pandas.DataFrame: DataFrame с данными сообщений.  Или None, если произошла ошибка.
    """
    try:
        # Вариант с Path
        json_file_path = Path(json_file_path)
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    except FileNotFoundError:
        print(f"Error: File not found: {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file: {json_file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    # Создаем DataFrame из списка сообщений
    df = pd.DataFrame(data['messages'])

    # Оставляем только нужные колонки (можно добавить/удалить по необходимости)
    df = df[['id', 'type', 'date', 'from', 'from_id', 'text', 'media_type', 'file', 'width', 'height', 'duration_seconds']]
    return df

# Пример использования (вариант с Path - РЕКОМЕНДУЕТСЯ)
file_path = Path('/mnt/c/Users/airve/Downloads/Telegram Desktop/ChatExport_2025-03-15 (1)/result.json')
print(f"File path: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")
print(f"Is file: {os.path.isfile(file_path)}")


df = load_telegram_export(file_path)

if df is not None:
    print(df.head())
    print(df.info())

