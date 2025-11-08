import os
import re
import json
import sqlite3
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import getpass

USER_NAME = getpass.getuser()
print("USER_NAME = " + USER_NAME)

# Получить текущий рабочий каталог
current_directory = os.getcwd()
print(f"Info:: Текущий каталог: {current_directory}")

# 41-MBA13-2018
# USER_NAME = "administrateur"
# USER_NAME = "maximebeauger"
# USER_NAME = "dionis"

# directory_path = "/Users/maximebeauger/Dropbox/SHARED/Project/PYTHON/LotScanner/test/alcopa_sales/sales"
# directory_path = "/Users/" + USER_NAME + "/Dropbox/SHARED/Project/PYTHON/LotScanner/data/_voiture/alcopa original/dates"
# directory_path = current_directory + "/_Files/Sales"
directory_path = "/Users/dionis/Project/Python/AlcopaScrapAuto/Session/SavedPage"
print(f"Info:: directory_path: {directory_path}")
#
# directory_path = "/Users/maximebeauger/Dropbox/SHARED/Project/PYTHON/LotScanner/data/_voiture/alcopa original/flash"
# directory_path = "/Users/maximebeauger/Dropbox/SHARED/Project/PYTHON/LotScanner/data/_voiture/alcopa original/multilist"

# PATH = "/Users/" + USER_NAME + "/Dropbox/SHARED/Project/PYTHON/LotScanner/test/alcopa_sales/08"
PATH = current_directory

# DB_PATH = 'alcopa_sales.db'
DB_PATH = current_directory + '/_Files/bdd/alcopa_sales.db'
print(f"Info:: DB_PATH: {DB_PATH}")

# DB_PATH = PATH + '/alcopa_sales.db'
LOG_PATH = PATH + '/_Files/logs/process_log.log'

# Создать файл лога, если он не существует
if not os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('')  # создаёт пустой файл

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Sales (
        id INTEGER PRIMARY KEY,
        id_number INTEGER UNIQUE,
        date TEXT,
        isCorrectionMode BOOLEAN,
        isEnded BOOLEAN,
        infocom TEXT,
        title TEXT,
        type TEXT,
        room TEXT
    );

    CREATE TABLE IF NOT EXISTS Product (
        id INTEGER PRIMARY KEY,
        model TEXT,
        name TEXT,
        openingBid INTEGER,
        mainImgUrl TEXT,
        lotId INTEGER UNIQUE,
        detailsUrl TEXT,
        highestBidValue INTEGER,
        lotNumber INTEGER,
        energy TEXT,
        mileage TEXT,
        rollout TEXT,
        gearbox TEXT,
        isActive BOOLEAN,
        type TEXT,
        decision TEXT,
        extraRound BOOLEAN,
        sale_id INTEGER,
        FOREIGN KEY (sale_id) REFERENCES Sales(id)
    );
    """)
    conn.commit()
    logging.info("Database initialized successfully.")
    return conn

def extract_json_from_html(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        script_tag = soup.find('script', string=re.compile(r'window\.__PRELOADED_STATE__'))
        if not script_tag:
            logging.warning(f"JSON data not found in {file_path}.")
            return None

        json_data_match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*\});?', script_tag.string)
        if not json_data_match:
            logging.warning(f"Failed to extract JSON data from {file_path}.")
            return None

        json_data = json.loads(json_data_match.group(1))
        logging.info(f"Successfully extracted JSON data.") # from {file_path}.")
        return json_data

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in extract_json_from_html: {e}")
        return None    

def extract_date_from_filename(filename):
    # Ищет дату в формате YYYY-MM-DD или YYYY-MM-DD HH-MM-SS в начале имени файла
    match = re.match(r"(\d{4}-\d{2}-\d{2})(?:[ _](\d{2}-\d{2}-\d{2}))?", filename)
    if match:
        date_str = match.group(1)
        return date_str
    return None

def insert_data(conn, json_data, filename=None):
    cursor = conn.cursor()

    try:
        sale = json_data.get('sale', {})
        sale_id_number = sale.get('id')

        # Получаем дату из имени файла, если возможно
        sale_date = None
        if filename:
            sale_date = extract_date_from_filename(filename)
            if sale_date:
                logging.info(f"Дата {sale_date} взята из имени файла.") #  : {filename}")
            else:
                sale_date = datetime.now().strftime('%Y-%m-%d')
                logging.warning(f"Дата не найдена в имени файла {filename}, используется текущая: {sale_date}")
        else:
            sale_date = datetime.now().strftime('%Y-%m-%d')
            logging.warning(f"Имя файла не передано, используется текущая дата: {sale_date}")

        sale_data = (
            sale_id_number,
            sale_date,
            sale.get('isCorrectionMode', False),
            sale.get('isEnded', False),
            sale.get('infocom', ''),
            sale.get('title', ''),
            sale.get('type', ''),
            sale.get('room', '')
        )

        cursor.execute("""
            INSERT OR IGNORE INTO Sales (
                id_number, date, isCorrectionMode, isEnded, infocom, title, type, room
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sale_data)
        logging.info(f"Inserted sale data for sale ID: {sale_id_number}")

        cursor.execute("SELECT id FROM Sales WHERE id_number = ?", (sale_id_number,))
        sale_id = cursor.fetchone()[0]

        lots = sale.get('lots', {})
        for lot in lots.values():
            details = lot.get('details', {})
            product_data = (
                lot.get("model"),
                lot.get("name"),
                lot.get("openingBid"),
                lot.get("mainImgUrl"),
                lot.get("lotId"),
                lot.get("detailsUrl"),
                lot.get("highestBidValue"),
                lot.get("lotNumber"),
                details.get("energy"),
                details.get("mileage"),
                details.get("rollout"),
                details.get("gearbox"),
                lot.get("isActive", False),
                lot.get("type"),
                lot.get("decision"),
                lot.get("extraRound", False),
                sale_id
            )

            cursor.execute("""
            INSERT OR IGNORE INTO Product (
                model, name, openingBid, mainImgUrl, lotId, detailsUrl,
                highestBidValue, lotNumber, energy, mileage, rollout,
                gearbox, isActive, type, decision, extraRound, sale_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, product_data)

        conn.commit()

    except Exception as e:
        logging.error(f"Error inserting data: {e}")

def process_files_recursively(directory_path):
    conn = create_database(DB_PATH)

    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith('.html'):
                file_path = os.path.join(root, filename)
                logging.info(f"Processing file: {filename}")
                # logging.info(f"Processing file: {file_path}")
                json_data = extract_json_from_html(file_path)
                if json_data:
                    insert_data(conn, json_data, filename=filename)
                logging.info(f" --- ")

    conn.close()
    logging.info("Data processing completed.")

# def process_files_in_directory(directory_path):
#     conn = create_database(DB_PATH)

#     for filename in os.listdir(directory_path):
#         if filename.endswith('.html'):
#             file_path = os.path.join(directory_path, filename)
#             print(f"Processing file: {filename}")
#             json_data = extract_json_from_html(file_path)
#             if json_data:
#                 insert_data(conn, json_data)

#     conn.close()
#     print("Data processing completed.")

if __name__ == "__main__":
    # directory_path = "/path/to/html/files"
    process_files_recursively(directory_path)
    # process_files_in_directory(directory_path)
