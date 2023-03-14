import psycopg2
from psycopg2 import sql

import re
from slugify import slugify

import json

class DataBase:
    def __init__(self, dbname, username, host, password, maintable_name="all_topics"):
        self.conn = psycopg2.connect(dbname=dbname,
        user=username, host=host,
        password=password)
        self.cur = self.conn.cursor()
        self.maintable_name = maintable_name
        self.conn.set_session(autocommit=True)
        self.create_table(self.maintable_name)
        self.contest_tables = self.get_contest_tables()
        self.transliterator = {"to_lat": {}, "to_cyr": {}}
        print("Database Initialized")
    
    def create_table(self, tablename: str):
        self.cur.execute(f"SELECT COUNT(1) FROM INFORMATION_SCHEMA.TABLES WHERE table_schema LIKE 'public' AND table_name='{tablename}'")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute(f"CREATE TABLE {tablename} (id varchar PRIMARY KEY, topic varchar, difficulty integer, solved_count integer)")
        
    def get_contest_tables(self):
        self.cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema LIKE 'public' AND table_name !='{self.maintable_name}'")
        tables = self.cur.fetchall()
        return tables
    
    def get_tables_by_name(self, name, name_type):
        if name_type==0:
            self.cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema LIKE 'public' AND table_name !='{self.maintable_name}' AND table_name LIKE '{name}%'")
        elif name_type==1:
            self.cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema LIKE 'public' AND table_name !='{self.maintable_name}' AND table_name LIKE '%{name}'")
        else:
            self.cur.execute(f"SELECT * FROM {self.maintable_name} WHERE {self.maintable_name}.id LIKE '%{name}%'")
        tables = self.cur.fetchall()
        return tables

    def count_records(self, tablename):
        query = sql.SQL("select * from {}").format(
            sql.Identifier(tablename))
        self.cur.execute(query)
        num = len(self.cur.fetchall())
        return num
    
    def format_topic(self, topic):
        topic_old = topic
        if re.search("[а-яА-Я]", topic):
            topic = slugify(topic)
        topic = ''.join(e for e in topic if e.isalpha())
        if topic not in self.transliterator["to_cyr"].keys():
            self.transliterator["to_cyr"][topic] = topic_old
            self.transliterator["to_lat"][topic_old] = topic
        return topic

    def update_contests(self, val:tuple):
        topics = val[1].split("; ")
        compare = []
        for topic in topics:
            topic = self.format_topic(topic)
            tablename = f"{topic}rating{val[2]}"
            if tablename not in self.contest_tables:
                self.create_table(tablename)
                self.cur.execute(f"INSERT INTO {tablename} VALUES ('{val[0]}', '{val[1]}', {val[2]}, {val[3]})")
                self.contest_tables.append(tablename)
                return
            compare.append((self.count_records(tablename), tablename))
        if compare != []:
            self.insert_to_table(min(compare, key=lambda x: x[0])[1], val)
        with open('transliterator.json', "w", encoding="UTF-8") as jsonfile:
            json.dump(self.transliterator, jsonfile, ensure_ascii=False, indent=4)

    def insert_to_table(self, tablename: str, val: tuple):
        self.cur.execute(f"SELECT COUNT(1) FROM {tablename} WHERE id='{val[0]}'")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute(f"INSERT INTO {tablename} VALUES ('{val[0]}', '{val[1]}', {val[2]}, {val[3]})")
            self.update_contests(val)
        else:
            self.cur.execute(f"UPDATE {tablename} SET difficulty={val[2]}, solved_count={val[3]} WHERE id='{val[0]}'")

    def get_random(self, tablename, n):
        n = min(n, 10)
        self.cur.execute(f"SELECT * FROM {tablename} ORDER BY random() LIMIT {n};")
        tables = self.cur.fetchall()
        return tables
