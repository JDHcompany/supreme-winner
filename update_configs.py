#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import random
import string
import requests
import time
from datetime import datetime

# ==================== НАСТРОЙКИ СВЯЗИ ====================
# Укажите прямую ссылку на файл best_files_links.txt из вашего ПЕРВОГО репозитория:
LINKS_MANIFEST_URL = "https://raw.githubusercontent.com/JDHcompany/ImprovedV/main/best_files_links.txt"
# Ссылка на вашего Telegram-бота (используется для отображения на сайте)
TG_CHANNEL_LINK = "https://t.me/freevpnconf_bot"
# ==========================================================

DATA_DIR = "data"
PHOTO_FILENAME = "image.jpg"


def get_best_urls_from_manifest(url):
    """Скачивает манифест-файл со ссылками и извлекает из него 2 прямые RAW/Pages ссылки."""
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
    """Скачивает содержимое конфигурационного файла и очищает его от HTML-тегов, если это был гибридный файл."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        text = response.text
        
        # Если скачанный файл уже является гибридным HTML, извлекаем из него чистые конфиги из верхнего блока комментариев
        if "<!--" in text and "-->" in text:
            match = re.search(r'<!--(.*?)-->', text, re.DOTALL)
            if match:
                return match.group(1).strip()
                
        return text
    except Exception as e:
        print(f"Ошибка при скачивании конфигов: {e}")
        return None


def generate_hybrid_html(plain_configs, part_idx):
    """
    Генерирует гибридный HTML-файл для отправки в Telegram.
    При открытии в браузере рендерит красивую страницу подписки.
    При чтении VPN-клиентом — считывает метаданные и прокси из скрытого блока в самом начале.
    """
    html_content = f"""<!--
{plain_configs}
-->
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍟 ImprovedVPN — Персональная подписка #{part_idx}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700;800&display=swap');
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #0b0f19;
        }}
        .glow-effect {{
            box-shadow: 0 0 25px -5px rgba(245, 158, 11, 0.3);
        }}
        .card-blur {{
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
    </style>
</head>
<body class="text-gray-100 min-h-screen flex flex-col justify-between selection:bg-amber-500 selection:text-black">
    <div class="absolute top-0 left-1/4 w-96 h-96 bg-amber-600/10 rounded-full blur-[100px] pointer-events-none"></div>
    <div class="absolute bottom-10 right-1/4 w-96 h-96 bg-orange-600/10 rounded-full blur-[100px] pointer-events-none"></div>

    <div class="max-w-xl w-full mx-auto px-4 py-16 z-10 my-auto">
        <div class="card-blur p-8 rounded-3xl glow-effect text-center border border-amber-500/20">
            <div class="inline-flex items-center justify-center p-3 bg-amber-500/10 rounded-2xl mb-6">
                <span class="text-4xl">🍟</span>
            </div>
            <h1 class="text-3xl font-extrabold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
                ImprovedVPN
            </h1>
            <p class="text-sm text-gray-400 mt-2">Ваша персональная подписка успешно загружена!</p>
            
            <div class="my-6 p-4 bg-gray-950/50 rounded-2xl border border-gray-800 text-left">
                <div class="text-xs text-gray-500">Тип подписки:</div>
                <div class="text-base font-bold text-white mt-1">🍟 Improved-potato #{part_idx}</div>
                <div class="text-xs text-gray-500 mt-3">Срок действия ссылок:</div>
                <div class="text-base font-bold text-amber-400 mt-1">Временная (Автоматическая ротация раз в 3 дня)</div>
            </div>

            <button onclick="copyCurrentUrl()" class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-600 text-black font-bold py-3.5 px-6 rounded-xl transition duration-200 transform hover:scale-[1.02]">
                <i data-lucide="copy" class="w-5 h-5"></i>
                Скопировать ссылку на подписку
            </button>

            <a href="{TG_CHANNEL_LINK}" target="_blank" class="mt-4 w-full flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 text-gray-300 font-bold py-3.5 px-6 rounded-xl transition duration-200 border border-gray-800">
                <i data-lucide="bot" class="w-5 h-5"></i>
                Наш Telegram-бот
            </a>
        </div>
    </div>

    <!-- Всплывающий тост -->
    <div id="toast" class="fixed bottom-5 right-5 transform translate-y-20 opacity-0 transition-all duration-300 ease-out z-50 flex items-center gap-3 bg-gray-950 text-white border border-green-500/30 px-5 py-4 rounded-2xl shadow-2xl">
        <div class="p-1 bg-green-500/20 text-green-400 rounded-lg">
            <i data-lucide="check" class="w-5 h-5"></i>
        </div>
        <div>
            <div class="font-bold text-sm">Ссылка скопирована!</div>
            <div class="text-xs text-gray-400 mt-0.5">Добавьте ее в Nekobox, Happ или V2rayN</div>
        </div>
    </div>

    <script>
        lucide.createIcons();
        function copyCurrentUrl() {{
            const el = document.createElement('textarea');
            el.value = window.location.href;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);

            const toast = document.getElementById('toast');
            toast.classList.remove('translate-y-20', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
            setTimeout(() => {{
                toast.classList.remove('translate-y-0', 'opacity-100');
                toast.classList.add('translate-y-20', 'opacity-0');
            }}, 3000);
        }}
    </script>
</body>
</html>"""
    return html_content


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


def send_message_with_buttons(token, chat_id, page_urls, update_time):
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
    for idx, file_url in enumerate(page_urls, 1):
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
    for idx, direct_url in enumerate(best_urls, 1):
        content = download_content(direct_url)

        if content:
            # Чтобы имена двух файлов не конфликтовали, но менялись раз в 3 дня:
            current_days_epoch = int(time.time() / 86400)
            three_day_period = (current_days_epoch // 3) + idx # добавляем сдвиг для второго файла
            random.seed(three_day_period)
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            random.seed(None)
            
            # Сохраняем файлы с расширением .html, чтобы они открывались в браузере как веб-страницы!
            new_name = f"config_{random_str}.html"
            file_path = os.path.join(DATA_DIR, new_name)

            # Формируем гибридное содержимое (конфиги/метаданные на первых строках, далее - HTML-код)
            hybrid_content = generate_hybrid_html(content, idx)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(hybrid_content)

            new_filenames.append(new_name)
            print(f"Сохранен файл #{idx}: {new_name}")
        else:
            print(f"Не удалось обновить файл #{idx}, пропускаем.")

    if len(new_filenames) < 2:
        print("Критическая ошибка: Не удалось обновить оба файла подписок.")
        sys.exit(1)

    # Формируем ссылки с использованием домена GitHub Pages
    if "/" in github_repository:
        username, repo_name = github_repository.split("/", 1)
        pages_url_base = f"https://{username}.github.io/{repo_name}"
    else:
        pages_url_base = f"https://raw.githubusercontent.com/{github_repository}/main"

    page_urls = []
    for file_name in new_filenames:
        page_url = f"{pages_url_base}/{DATA_DIR}/{file_name}"
        page_urls.append(page_url)
        print(f"Ссылка GitHub Pages: {page_url}")

    update_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Формируем ссылку на картинку (картинку можно оставить на RAW)
    photo_url = f"https://raw.githubusercontent.com/{github_repository}/main/{PHOTO_FILENAME}"
    print(f"Ссылка на картинку: {photo_url}")

    # 1. Отправляем картинку
    print("Отправка картинки...")
    photo_sent = send_photo_only(telegram_token, telegram_to_id, photo_url)
    
    if not photo_sent:
        print("Не удалось отправить картинку, но продолжаем...")

    # 2. Отправляем сообщение с кнопками (кнопки ведут на GitHub Pages страницы)
    print("Отправка сообщения с кнопками...")
    message_sent = send_message_with_buttons(telegram_token, telegram_to_id, page_urls, update_time)
    
    if not message_sent:
        sys.exit(1)
    
    print("Готово!")


if __name__ == "__main__":
    main()
