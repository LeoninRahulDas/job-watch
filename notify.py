# notify.py - send a Telegram message
import os

import requests


def send(text):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print(text)           # no Telegram set up yet: show the alert on screen
        print('-' * 40)
        return True
    try:
        r = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': text[:4000], 'disable_web_page_preview': True},
            timeout=20,
        )
        return r.ok
    except requests.RequestException as e:
        print(f'[warn] telegram failed: {e}')
        return False
