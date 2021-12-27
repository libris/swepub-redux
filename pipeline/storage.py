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

    # Because the APIs expose publications as originally harvestes, these must be kept.
    cursor.execute("""
    CREATE TABLE original (
        id INTEGER PRIMARY KEY,
        data TEXT
    );
    """)

    # After conversion, validation and normalization each publication is stored in this
    # form, for later in use in deduplication.
    cursor.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        data TEXT,
        original_id INTEGER,
        FOREIGN KEY (original_id) REFERENCES original(id)
    );
    """)

    # To facilitate deduplication, store all of each publications ids (regardless of type)
    # in this table. This includes (a mangled form of) maintitles. Grouping on
    # 'identifier' in this table, will produce the raw candidates for deduplication.
    # These, to be clear, will overlap. But overlaping clusters will be joined in a later
    # step. This table should be considered temporary and dropped after deduplication.
    cursor.execute("""
    CREATE TABLE clusteringidentifiers (
        id INTEGER PRIMARY KEY,
        identifier TEXT,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
    );
    """)

    connection.commit()

def open_existing_storage():
    global connection
    connection = sqlite3.connect(sqlite_path)

def store_converted(xml, converted):
    cursor = connection.cursor()

    #print(f'Inserting with oai_id {converted["@id"]}')

    original_rowid = cursor.execute("""
    INSERT INTO original(data) VALUES(?);
    """, (json.dumps(converted),)).lastrowid

    converted_rowid = cursor.execute("""
    INSERT INTO converted(data, original_id) VALUES(?, ?);
    """, (json.dumps(converted), original_rowid)).lastrowid

    identifiers = []
    for title in converted["instanceOf"]["hasTitle"]:
        if title["mainTitle"] is not None and isinstance(title["mainTitle"], str):
            identifiers.append(title["mainTitle"]) # TODO: STRIP AWAY WHITESPACE ETC
    
    for id_object in converted["identifiedBy"]:
        identifier = id_object["value"]
        if identifier is not None and isinstance(identifier, str):
            identifiers.append(identifier)
            
    for identifier in identifiers:
        cursor.execute("""
        INSERT INTO clusteringidentifiers(identifier, converted_id) VALUES (?, ?)
        """, (identifier, converted_rowid))
            
    connection.commit()

def get_cursor():
    return connection.cursor()
