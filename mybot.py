import os
import telebot
from dotenv import load_dotenv
from mydb import DataBase
from myparser import TheParser

import json


class TheTeleBot():
    def __init__(self, db: DataBase):
        load_dotenv()
        API_KEY = os.getenv("API_KEY")
        bot = telebot.TeleBot(API_KEY)

        self.db = db

        self.contest_tables = set(map(lambda x: x[0], db.get_contest_tables()))
        self.transliterator = {"to_lat": {}, "to_cyr": {}}
        
        print("Telegram Bot Initialized\n  *\n **\n***\n **\n  *")
        try:
            with open("transliterator.json", "r", encoding="UTF-8") as jsonfile:
                self.transliterator = json.load(jsonfile)
        except Exception as e:
            print(e)
            someParser = TheParser(self.db)
            print("Starting Parsing...")
            someParser.insert_all_to_db()

        def start_markup():
            markup =telebot.types.InlineKeyboardMarkup(row_width=2)
            
            item_topic = telebot.types.InlineKeyboardButton("Тема задания", callback_data="topic")
            item_rating = telebot.types.InlineKeyboardButton("Сложность задания", callback_data="difficulty")

            markup.add(item_topic, item_rating)
            return markup
        
        @bot.callback_query_handler(func = lambda call: True)
        def callback(call):
            if call.message:
                if call.data=="topic":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите тему", reply_markup=topic_difficulty_markup(1))
                    pass
                elif call.data=="difficulty":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите сложность", reply_markup=topic_difficulty_markup(2))
                elif call.data=="home":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Главное меню", reply_markup=start_markup())
                elif call.data in self.transliterator["to_cyr"].keys():
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Выберите сложность для темы {call.message.text}", reply_markup=topic_difficulty_markup(3, text=call.data))
                elif str(call.data).isnumeric():
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Выберите тему для сложности {call.data}", reply_markup=topic_difficulty_markup(4, text=call.data))
                elif str(call.data) in self.contest_tables:
                    tablename = str(call.data)
                    n = db.count_records(tablename)
                    items = db.get_random(tablename, n)
                    items = list(map(format_output, items))
                    joined_items = ".\n\n".join(items)
                    topic_in_cyr = self.transliterator["to_cyr"][tablename.split("rating")[0]]
                    difficulty = tablename.split("rating")[1]
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Задачи по теме:{topic_in_cyr}, сложность:{difficulty} :\n\n {joined_items}", reply_markup=start_markup())

        
        def format_output(item):
            item = str(item[0]) +" темы: "+ str(item[1]) +" сложность: " + str(item[2]) + " кол-во решивших: " + str(item[3])
            return item
        
        def topic_difficulty_markup(num, text=""):
            markup =telebot.types.InlineKeyboardMarkup(row_width=3)
            buttons = []
            if num<3:
                if num == 1:
                    params = sorted(set(self.transliterator["to_lat"].keys()), key=lambda x:str(x[0]))
                    buttons = [telebot.types.InlineKeyboardButton(param, callback_data=self.transliterator["to_lat"][param]) for param in params]
                elif num == 2:
                    params = sorted(set(map(lambda x: x[0].split("rating")[1], db.get_contest_tables())), key=lambda x: int(x))
                    buttons = [telebot.types.InlineKeyboardButton(param, callback_data=param) for param in params]
            elif num == 3:
                params = sorted(set(map(lambda x: x[0].split("rating")[1], db.get_tables_by_name(text, 0))), key=lambda x: int(x))
                buttons = [telebot.types.InlineKeyboardButton(param, callback_data=f"{text}rating{param}") for param in params]
            elif num == 4:
                params = sorted(set(map(lambda x: x[0].split("rating")[0], db.get_tables_by_name(text, 1))), key=lambda x: str(x[0]))
                buttons = [telebot.types.InlineKeyboardButton(self.transliterator["to_cyr"][param], callback_data=f"{param}rating{text}") for param in params]
            params.append("Home")
            buttons.append(telebot.types.InlineKeyboardButton("Home", callback_data="home"))
            markup.add(*buttons)
            return markup
        

        @bot.message_handler(content_types=['text'])
        def get_text_message(message):
            if message:
                if message.text=="/start":
                    bot.send_message(message.chat.id, "Главное меню", reply_markup=start_markup())
                elif message.text=="/help":
                    bot.send_message(message.chat.id, "Выберите тему и сложность задания, чтобы получить задания по соответсвующему контесту\n\nДля поиска заданий:Введите в чат название задания, которое хотите найти.")
                elif str(message.text).isalnum():
                    tablename = str(message.text)
                    items = db.get_tables_by_name(tablename, 2)
                    if items != []:
                        items = list(map(lambda x: " ".join(list(map(lambda y: str(y), x))), items))
                        joined_items = "\n".join(items)
                        bot.send_message(chat_id=message.chat.id, text=f"{joined_items}")
                    else:
                        bot.send_message(chat_id=message.chat.id, text=f"Задание {tablename} не найдено")

        bot.polling()


if __name__ == "__main__":
    myDB = DataBase(dbname="tasksDB", username="postgres", host="localhost", password="postgrepassword")
    myBot = TheTeleBot(myDB)

