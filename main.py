from threading import Thread

from sched import scheduler
import time

from myparser import TheParser
from mydb import DataBase
from mybot import TheTeleBot

def periodicParse():
    print("periodicParse")
    s.enter(3600, 1, myParser.insert_all_to_db, argument=())
    s.run()
    print("SCHEDULED THING HAPPENED")

def startWork(parse_before: bool):
    print("startword")
    if parse_before:
        myParser.insert_all_to_db()
    print("all inserted")
    thread_periodic.start()
    thread_bot.start()

def doBotWork():
    print("doBotWork")
    myBot = TheTeleBot(myDB)


if __name__ == "__main__":
    s = scheduler(time.time, time.sleep)
    myDB = DataBase(dbname="tasksDB", username="postgres", host="localhost", password="postgrepassword")
    myParser = TheParser(myDB)
    thread_bot = Thread(target=doBotWork())
    thread_periodic = Thread(target=periodicParse())
    startWork(False)
