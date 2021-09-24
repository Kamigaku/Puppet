import os
import sqlite3

from peewee import *

from discordClient.meta.singletonMeta import SingletonMeta


class DbContext(metaclass=SingletonMeta):

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
