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

        # self.sqliteConnection = sqlite3.connect('db\\database.db')
        # cursor = self.sqliteConnection.cursor()
        # print("Successfully Connected to SQLite")
        #
        # with open('db\\table_creations.sql', 'r') as sqlite_file:
        #     sql_script = sqlite_file.read()
        # cursor.executescript(sql_script)
        # print("SQLite script executed successfully")
        # cursor.close()

        # models definitions
        # self.characters = {}
        # self.affiliations = {}
        # self.background = {}
        #
        # retrieved_obj = character.retrieve_characters()
        # for char in retrieved_obj:
        #     c = character.Character(char)
        #     self.characters[c.id] = c
        #
        # retrieved_obj = affiliation.retrieve_affiliations()
        # for aff in retrieved_obj:
        #     a = affiliation.Affiliation(aff)
        #     self.affiliations[a.id] = a
        #
        # retrieved_obj = background.retrieve_backgrounds()
        # for bg in retrieved_obj:
        #     b = background.Background(bg)
        #     self.background[b.id] = b
        #
        # retrieved_obj = self.execute_select("SELECT * FROM appearance")
        # for app in retrieved_obj:
        #     self.characters[app[0]].associated_background.append(self.background[app[1]])
        #     self.background[app[1]].associated_character.append(self.characters[app[0]])
        #
        # retrieved_obj = self.execute_select("SELECT * FROM appearance")
        # for app in retrieved_obj:
        #     self.characters[app[0]].associated_affiliation.append(self.affiliations[app[1]])
        #     self.affiliations[app[1]].associated_character.append(self.characters[app[0]])

    def close_db(self):
        if self.sqliteConnection:
            self.sqliteConnection.close()
