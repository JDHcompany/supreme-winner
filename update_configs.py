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

# Название файла с картинкой в репозитории (положите её в корень или в data/)
PHOTO_FILENAME = "image.jpg"  # Замените на имя вашей картинки
# Если картинка в папке data, то напишите: PHOTO_FILENAME = "data/image.jpg"


def decode_url(encoded_str):
    """Декодирует URL-адрес из Base64."""
    try:
        decoded_bytes = base64.b64decode(encoded_str.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        print(f"Ошибка декодирования URL: {e}")
        sys.exit(1)


def generate_random_filename():
    """Генерирует случайное имя файла (config_[12 случайных символов].txt)."""
    random_str = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=12))
    return f"config_{random_str}.txt"


def clean_old_files():
    """Удаляет старые конфигурационные файлы из папки данных."""
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
        print(f"Ошибка при скачивании файла с {url}: {e}")
        return None


def send_telegram_post_with_photo(token, chat_id, raw_urls, update_time, github_repository):
    """Отправляет фото из репозитория, а под ним сообщение с кнопками."""
    
    # Формируем прямую ссылку на картинку в репозитории
    photo_url = f"https://raw.githubusercontent.com/{github_repository}/main/{PHOTO_FILENAME}"
    
    # Сначала отправляем фото
    photo_api_url = f"https://api.telegram.org/bot{token}/sendPhoto"
    photo_payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": "🔄 **Конфигурации обновлены!**",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(photo_api_url, json=photo_payload, timeout=20)
        response.raise_for_status()
        print("Фото успешно отправлено!")
    except Exception as e:
        print(f"Ошибка при отправке фото: {e}")
        print(f"Проверьте, что файл {PHOTO_FILENAME} существует в репозитории")
        # Продолжаем выполнение даже если фото не отправилось

    # Формируем текст сообщения
    message_text = (
        f"🆕 **Обновление конфигураций**\n"
        f"🕒 **Время обновления:** `{update_time}`\n\n"
        f"👇 **Нажми на кнопку, чтобы скопировать конфиг:**\n\n"
        f"🗃️ **Больше новых конфигов в моем боте** 🎁 - @freevpnconf_bot"
    )

    # Формируем inline-клавиатуру: 6 кнопок в один столбик
    inline_keyboard = []
    for idx, file_url in enumerate(raw_urls, 1):
        inline_keyboard.append([{
            "text": f"📋 Скопировать Конфиг #{idx}",
            "url": file_url
        }])

    # Отправляем текстовое сообщение с кнопками
    message_api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    message_payload = {
        "chat_id": chat_id,
        "text": message_text,
        "reply_markup": {
            "inline_keyboard": inline_keyboard
        },
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(message_api_url, json=message_payload, timeout=20)
        response.raise_for_status()
        print("Пост успешно опубликован в Telegram!")
    except Exception as e:
        print(f"Ошибка при публикации поста в Telegram: {e}")
        sys.exit(1)


def main():
    # Безопасное считывание секретов из окружения (GitHub Secrets)
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_to_id = os.environ.get("TELEGRAM_TO_ID")
    github_repository = os.environ.get("GITHUB_REPOSITORY")

    if not telegram_token or not telegram_to_id:
        print("Ошибка: Переменные окружения TELEGRAM_TOKEN или TELEGRAM_TO_ID не найдены.")
        sys.exit(1)

    if not github_repository:
        print("Ошибка: Переменная GITHUB_REPOSITORY пуста.")
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
            print(f"Сохранен новый файл #{idx}: {new_name}")
        else:
            print(f"Не удалось обновить файл #{idx}, пропускаем.")

    if not new_filenames:
        print("Критическая ошибка: Ни один файл не был обновлен.")
        sys.exit(1)

    # Генерация прямых raw-ссылок на созданные файлы
    raw_urls = []
    for file_name in new_filenames:
        raw_url = f"https://raw.githubusercontent.com/{github_repository}/main/{DATA_DIR}/{file_name}"
        raw_urls.append(raw_url)

    # Получаем текущее время
    update_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Отправка фото + поста в Telegram
    print("Публикация фото и поста...")
    send_telegram_post_with_photo(telegram_token, telegram_to_id, raw_urls, update_time, github_repository)


if __name__ == "__main__":
    main()
