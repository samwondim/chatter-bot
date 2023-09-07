import os
import urllib
import telebot
import json
import requests
import time

from dbhelper import DBHelper
db = DBHelper()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
URL = "https://api.telegram.org/bot{}/".format(BOT_TOKEN)

# bot = telebot.TeleBot(BOT_TOKEN)

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")

    return content

def get_json_form_url(url):
    content = get_url(url)
    js = json.loads(content)

    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_form_url(url)

    return js

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]

    return (text, chat_id)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?chat_id={}&text={}&parse_mode=Markdown".format(chat_id, text)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def get_last_update_id(updates):
    update_ids = []
    for update_id in updates["result"]:
        update_ids.append(int(update_id["update_id"]))
    
    return max(update_ids)

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard":True}
    
    return json.dumps(reply_markup)

def handle_updates(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            items = db.get_items(chat) ##

            if text.lower() == "/done":
                keyboard = build_keyboard(items)
                send_message("Select an item to delete", chat, keyboard)
            elif text in items:
                db.delete_item(text, chat) ##
                items = db.get_items(chat) ##
                keyboard = build_keyboard(items)
                send_message("Select an item to delete", chat, keyboard)
            elif text.lower() == "/start":
                send_message("Welcome to your personal TO DO LIST. Send Any text to me and I will store it as an item. Send /done to start removing items", chat)
            elif text.lower() == '/clear':
                db.clear(chat)
                send_message("Looks like your to do list is empty :(", chat)
            elif text.startswith("/"):
                continue    
            else:
                db.add_item(text, chat)##
                items = db.get_items(chat) ##
                message = "\n".join(items)
                send_message(message, chat)
        except KeyError:
            pass

def main():
    db.setup()
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
