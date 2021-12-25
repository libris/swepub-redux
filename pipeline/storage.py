import sqlite3
from sqlite3.dbapi2 import connect
import json
import os

sqlite_path = "./swepub.sqlite3"

connection = None

def clean_and_init_storage():
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    global connection
    connection = sqlite3.connect(sqlite_path, timeout=(5*60))
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        cluster INTEGER,
        oai_id TEXT,
        data TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE maintitle (
        maintitle TEXT,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
    );
    """)
    connection.commit()

def open_existing_storage():
    global connection
    connection = sqlite3.connect(sqlite_path)

def store_converted(converted):
    cursor = connection.cursor()

    #print(f'Inserting with oai_id {converted["@id"]}')

    converted_id = cursor.execute("""
    INSERT INTO converted(cluster, oai_id, data) VALUES(?, ?, ?);
    """, (-1, converted["@id"], json.dumps(converted))).lastrowid

    for title in converted["instanceOf"]["hasTitle"]:
        if title["mainTitle"] is not None and isinstance(title["mainTitle"], str):
            cursor.execute("""
            INSERT INTO maintitle VALUES (?, ?)
            """, (title["mainTitle"], converted_id))

    connection.commit()

def get_cursor():
    return connection.cursor()
