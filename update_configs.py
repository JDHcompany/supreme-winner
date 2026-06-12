#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import requests
from datetime import datetime

# ==================== НАСТРОЙКИ СВЯЗИ ====================
# Прямая RAW-ссылка на файл best_files_links.txt из вашего ПЕРВОГО репозитория:
LINKS_MANIFEST_URL = "https://raw.githubusercontent.com/JDHcompany/ImprovedV/main/best_files_links.txt"
# ==========================================================

PHOTO_FILENAME = "image.jpg"


def get_best_urls_from_manifest(url):
    """Скачивает манифест-файл со ссылками и извлекает из него готовые ссылки GitHub Pages."""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        content = response.text
        
        # Ищем все URL-адреса в тексте
        urls = re.findall(r'https?://[^\s]+', content)
        
        # Фильтруем ссылки, оставляя только те, которые содержат файлы лучших конфигураций (best_1, best_2)
        clean_urls = [u.strip() for u in urls if "best_" in u]
        
        if len(clean_urls) < 2:
            print(f"Предупреждение: Найдено меньше 2 ссылок в файле ({len(clean_urls)} шт). Пробуем вернуть все найденные.")
            clean_urls = [u.strip() for u in urls if u.strip()]
            
        return clean_urls[:2]  # Возвращаем ровно 2 ссылки
    except Exception as e:
        print(f"Ошибка при получении манифеста ссылок: {e}")
        return []


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


def send_message_with_copyable_links(token, chat_id, raw_urls, update_time):
    """
    Отправляет текстовое сообщение, где ссылки оформлены через HTML-тег <code>.
    При нажатии на такую ссылку в Telegram она автоматически копируется в буфер обмена.
    """
    url1 = raw_urls[0] if len(raw_urls) > 0 else ""
    url2 = raw_urls[1] if len(raw_urls) > 1 else ""

    # Формируем текст сообщения с использованием HTML-разметки.
    # Тег <code> делает текст моноширинным и кликабельным для быстрого копирования.
    message_text = (
        f"🆕 <b>Обновление конфигураций</b>\n"
        f"🕒 Время обновления: {update_time}\n\n"
        f"🎁 Больше конфигов в боте — @freevpnconf_bot\n\n"
        f"👇 <b>НАЖМИ НА ССЫЛКУ НИЖЕ, ЧТОБЫ СКОПИРОВАТЬ:</b>\n\n"
        f"🍟 <b>Конфиг #1 (Нажмите для копирования):</b>\n"
        f"<code>{url1}</code>\n\n"
        f"⚡ <b>Конфиг #2 (Нажмите для копирования):</b>\n"
        f"<code>{url2}</code>" 
    )

    # Кнопки под сообщением ведут на красивую веб-страницу (как запасной вариант)
    inline_keyboard = [
        [{"text": "🌐 Открыть веб-страницу #1", "url": url1}],
        [{"text": "🌐 Открыть веб-страницу #2", "url": url2}]
    ]

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "HTML",  # Указываем HTML-парсинг для работы тегов <code> и <b>
        "reply_markup": {"inline_keyboard": inline_keyboard}
    }

    try:
        response = requests.post(api_url, json=payload, timeout=20)
        response.raise_for_status()
        print("Сообщение успешно отправлено в Telegram!")
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

    print("Скачивание актуальных ссылок из первого репозитория...")
    best_urls = get_best_urls_from_manifest(LINKS_MANIFEST_URL)
    
    if not best_urls or len(best_urls) < 2:
        print("Критическая ошибка: Не удалось получить 2 ссылки на лучшие файлы.")
        sys.exit(1)

    print(f"Успешно получены ссылки:")
    for idx, url in enumerate(best_urls, 1):
        print(f"Ссылка #{idx}: {url}")

    update_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Формируем ссылку на обложку (картинку)
    photo_url = f"https://raw.githubusercontent.com/{github_repository}/main/{PHOTO_FILENAME}"
    print(f"Ссылка на картинку: {photo_url}")

    # 1. Отправляем картинку в канал
    print("Отправка картинки...")
    photo_sent = send_photo_only(telegram_token, telegram_to_id, photo_url)
    
    if not photo_sent:
        print("Не удалось отправить картинку, но продолжаем отправку текста...")

    # 2. Отправляем сообщение с копируемыми ссылками и кнопками перехода
    print("Отправка сообщения...")
    message_sent = send_message_with_copyable_links(telegram_token, telegram_to_id, best_urls, update_time)
    
    if not message_sent:
        print("Ошибка: Не удалось отправить сообщение в Telegram.")
        sys.exit(1)
    
    print("Всё успешно отправлено!")


if __name__ == "__main__":
    main()
