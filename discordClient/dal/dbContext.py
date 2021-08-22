import sqlite3
import os
from peewee import *
import discordClient.meta.singletonMeta as singletonMeta


class DbContext(metaclass=singletonMeta.SingletonMeta):

    def __init__(self):
        try:
            self.sqliteConnection = SqliteDatabase("db" + os.sep + "database.db")
            self.sqliteConnection.connect()
        except sqlite3.Error as error:
            self.close_db()
            print("Error while executing sqlite script", error)

    def close_db(self):
        if self.sqliteConnection:
            self.sqliteConnection.close()
