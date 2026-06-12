#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import random
import string
import requests
from datetime import datetime

# ==================== НАСТРОЙКИ СВЯЗИ ====================
# Укажите прямую RAW-ссылку на файл best_files_links.txt из вашего ПЕРВОГО репозитория:
LINKS_MANIFEST_URL = "https://raw.githubusercontent.com/JDHcompany/ImprovedV/main/best_files_links.txt"
# ==========================================================

DATA_DIR = "data"
PHOTO_FILENAME = "image.jpg"


def get_best_urls_from_manifest(url):
    """Скачивает манифест-файл со ссылками и извлекает из него 2 прямые RAW ссылки."""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        content = response.text
        
        # Находим все строки, начинающиеся с http
        urls = re.findall(r'https?://[^\s]+', content)
        # Очищаем от возможных комментариев или лишних символов
        clean_urls = [u.strip() for u in urls if "best_" in u]
        
        if len(clean_urls) < 2:
            print(f"Предупреждение: Найдено меньше 2 ссылок в файле ({len(clean_urls)} шт). Пробуем забрать любые доступные.")
            clean_urls = [u.strip() for u in urls if u.strip()]
            
        return clean_urls[:2] # Возвращаем ровно 2 ссылки
    except Exception as e:
        print(f"Ошибка при получении манифеста ссылок: {e}")
        return []


def generate_seeded_filename():
    """
    Генерирует случайное имя файла, которое меняется ровно раз в 3 дня.
    Использует текущую эпоху дней деленную на 3 в качестве seed для random.
    """
    # Вычисляем количество дней, прошедших с начала эпохи
    current_days_epoch = int(time.time() / 86400)
    # Группируем дни по 3. Каждые 3 дня значение этой переменной будет меняться
    three_day_period = current_days_epoch // 3
    
    # Инициализируем генератор случайных чисел уникальным ключом этого трехдневного периода
    random.seed(three_day_period)
    
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    # Сбрасываем seed обратно на системный генератор, чтобы другие вызовы были действительно случайными
    random.seed(None)
    
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
        print(f"Ошибка при скачивании конфигов: {e}")
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
    """Отправляет текстовое сообщение с ровно 2 кнопками (Текст сообщения не изменен)."""
    
    message_text = (
        f"🆕 Обновление конфигураций\n"
        f"🕒 Время обновления: {update_time}\n\n"
        f"🗃️ Больше новых конфигов в моем боте 🎁 - @freevpnconf_bot\n\n"
        f"⏳ Ссылки работают 12 часов, а потом обновляются 🔄\n\n"
        f"👇 Нажми на кнопку, чтобы скопировать конфиг:"
    )

    inline_keyboard = []
    # Выводим ровно 2 кнопки
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


import time # Импортируем модуль времени для расчета эпохи дней

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

    print("Скачивание ссылок из первого проекта...")
    best_urls = get_best_urls_from_manifest(LINKS_MANIFEST_URL)
    
    if not best_urls:
        print("Критическая ошибка: Не удалось получить ссылки на лучшие файлы.")
        sys.exit(1)

    print(f"Успешно извлечено {len(best_urls)} ссылок.")

    print("Очистка старых файлов...")
    clean_old_files()

    new_filenames = []
    
    print("Скачивание актуальных конфигураций...")
    # Генерируем уникальное имя на основе ротируемого 3-дневного сида
    # Для первой ссылки генерируем одно имя, а добавив индекс к сиду, сгенерируем второе
    for idx, direct_url in enumerate(best_urls, 1):
        content = download_content(direct_url)

        if content:
            # Чтобы имена двух файлов не конфликтовали, но менялись раз в 3 дня:
            current_days_epoch = int(time.time() / 86400)
            three_day_period = (current_days_epoch // 3) + idx # добавляем сдвиг для второго файла
            random.seed(three_day_period)
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            random.seed(None)
            
            new_name = f"config_{random_str}.txt"
            file_path = os.path.join(DATA_DIR, new_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            new_filenames.append(new_name)
            print(f"Сохранен файл #{idx}: {new_name}")
        else:
            print(f"Не удалось обновить файл #{idx}, пропускаем.")

    if len(new_filenames) < 2:
        print("Критическая ошибка: Не удалось обновить оба файла подписок.")
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

    # 2. Отправляем сообщение с кнопками (ровно 2 кнопки)
    print("Отправка сообщения с кнопками...")
    message_sent = send_message_with_buttons(telegram_token, telegram_to_id, raw_urls, update_time)
    
    if not message_sent:
        sys.exit(1)
    
    print("Готово!")


if __name__ == "__main__":
    main()
