import os
import sys
import base64
import random
import string
import requests
from datetime import datetime

# Исходные ссылки на конфигурации, закодированные в Base64
ENCODED_URLS = [
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0pESGNvbXBhbnkvY3Jpc3B5LWJyb2Njb2xpL3JlZnMvaGVhZHMvbWFpbi9yZXN1bHRzL3RvcF9zcGxpdC90b3BfcGFydF8xLnR4dA==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0pESGNvbXBhbnkvY3Jpc3B5LWJyb2Njb2xpL3JlZnMvaGVhZHMvbWFpbi9yZXN1bHRzL3RvcF9zcGxpdC90b3BfcGFydF8yLnR4dA==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0pESGNvbXBhbnkvY3Jpc3B5LWJyb2Njb2xpL3JlZnMvaGVhZHMvbWFpbi9yZXN1bHRzL3RvcF9zcGxpdC90b3BfcGFydF8zLnR4dA==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0pESGNvbXBhbnkvY3Jpc3B5LWJyb2Njb2xpL3JlZnMvaGVhZHMvbWFpbi9yZXN1bHRzL3RvcF9zcGxpdC90b3BfcGFydF80LnR4dA==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0pESGNvbXBhbnkvY3Jpc3B5LWJyb2Njb2xpL3JlZnMvaGVhZHMvbWFpbi9yZXN1bHRzL3RvcF9zcGxpdC90b3BfcGFydF81LnR4dA==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0pESGNvbXBhbnkvY3Jpc3B5LWJyb2Njb2xpL3JlZnMvaGVhZHMvbWFpbi9yZXN1bHRzL3RvcF9zcGxpdC90b3BfcGFydF82LnR4dA=="
]

DATA_DIR = "data"

# НАЗВАНИЕ ВАШЕЙ КАРТИНКИ (положите её в корень репозитория)
PHOTO_FILENAME = "image.jpg"


def decode_url(encoded_str):
    """Декодирует URL-адрес из Base64."""
    try:
        decoded_bytes = base64.b64decode(encoded_str.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        print(f"Ошибка декодирования URL: {e}")
        sys.exit(1)


def generate_random_filename():
    """Генерирует случайное имя файла."""
    random_str = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=12))
    return f"config_{random_str}.txt"


def clean_old_files():
    """Удаляет старые конфигурационные файлы."""
    if os.path.exists(DATA_DIR):
        for file in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Не удалось удалить файл {file_path}: {e}")
    else:
        os.makedirs(DATA_DIR)


def download_content(url):
    """Скачивает содержимое конфигурационного файла."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        return None


def send_photo_only(token, chat_id, photo_url):
    """Отправляет только картинку (без подписи)."""
    api_url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=20)
        response.raise_for_status()
        print("Картинка успешно отправлена!")
        return True
    except Exception as e:
        print(f"Ошибка при отправке картинки: {e}")
        return False


def send_message_with_buttons(token, chat_id, raw_urls, update_time):
    """Отправляет текстовое сообщение с кнопками (БЕЗ Markdown)."""
    
    # Простой текст без Markdown разметки
    message_text = (
        f"🆕 Обновление конфигураций\n"
        f"🕒 Время обновления: {update_time}\n\n"
        f"🗃️ Больше новых конфигов в моем боте 🎁 - @freevpnconf_bot/n/n"
        f"⏳ссылки работают 12 часов,а потом обновляются🔄/n/n"
        f"👇 Нажми на кнопку, чтобы скопировать конфиг:"
    )

    inline_keyboard = []
    for idx, file_url in enumerate(raw_urls, 1):
        inline_keyboard.append([{
            "text": f"📋 Скопировать Конфиг #{idx}",
            "url": file_url
        }])

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "reply_markup": {"inline_keyboard": inline_keyboard}
        # Убрал parse_mode - теперь точно нет проблем с Markdown
    }

    try:
        response = requests.post(api_url, json=payload, timeout=20)
        response.raise_for_status()
        print("Сообщение с кнопками успешно отправлено!")
        return True
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Ответ Telegram: {e.response.text}")
        return False


def main():
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_to_id = os.environ.get("TELEGRAM_TO_ID")
    github_repository = os.environ.get("GITHUB_REPOSITORY")

    if not telegram_token or not telegram_to_id:
        print("Ошибка: TELEGRAM_TOKEN или TELEGRAM_TO_ID не найдены.")
        sys.exit(1)

    if not github_repository:
        print("Ошибка: GITHUB_REPOSITORY пуста.")
        sys.exit(1)

    print("Очистка старых файлов...")
    clean_old_files()

    new_filenames = []
    
    print("Скачивание актуальных конфигураций...")
    for idx, encoded_url in enumerate(ENCODED_URLS, 1):
        direct_url = decode_url(encoded_url)
        content = download_content(direct_url)

        if content:
            new_name = generate_random_filename()
            file_path = os.path.join(DATA_DIR, new_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            new_filenames.append(new_name)
            print(f"Сохранен файл #{idx}: {new_name}")
        else:
            print(f"Не удалось обновить файл #{idx}, пропускаем.")

    if not new_filenames:
        print("Критическая ошибка: Ни один файл не был обновлен.")
        sys.exit(1)

    # Генерация ссылок на конфиги
    raw_urls = []
    for file_name in new_filenames:
        raw_url = f"https://raw.githubusercontent.com/{github_repository}/main/{DATA_DIR}/{file_name}"
        raw_urls.append(raw_url)

    update_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Формируем ссылку на картинку
    photo_url = f"https://raw.githubusercontent.com/{github_repository}/main/{PHOTO_FILENAME}"
    print(f"Ссылка на картинку: {photo_url}")

    # 1. Отправляем картинку
    print("Отправка картинки...")
    photo_sent = send_photo_only(telegram_token, telegram_to_id, photo_url)
    
    if not photo_sent:
        print("Не удалось отправить картинку, но продолжаем...")

    # 2. Отправляем сообщение с кнопками
    print("Отправка сообщения с кнопками...")
    message_sent = send_message_with_buttons(telegram_token, telegram_to_id, raw_urls, update_time)
    
    if not message_sent:
        sys.exit(1)
    
    print("Готово!")


if __name__ == "__main__":
    main()
