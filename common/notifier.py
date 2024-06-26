# notifier.py
import os

import requests


def send_to_telegram(msg):
    message = "" + str(os.getpid()) + " : " + msg
    api_token = os.environ.get("TELEGRAM_API_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    api_url = f'https://api.telegram.org/bot{api_token}/sendMessage'

    try:
        response = requests.post(api_url,
                                 json={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'})
        print(response.text)
    except Exception as e:
        print(e)

def send_photo_to_telegram(msg, photo_path):
    message = "" + str(os.getpid()) + " : " + msg
    api_token = os.environ.get("TELEGRAM_API_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    api_url = f'https://api.telegram.org/bot{api_token}/sendPhoto'

    try:
        files = {'photo': open(photo_path, 'rb')}
        data = {'chat_id': chat_id, 'caption': message}
        response = requests.post(api_url, files=files, data=data)
        print(response.text)
    except Exception as e:
        print(e)


class Notifier:
    def __init__(self, name, dog):
        self.name = name
        self.dog = dog
        send_to_telegram("Hello from Python!")
