import os
import re
import json
import sqlite3
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# directory_path = "/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/test/alcopa_sales/sales"
directory_path = "/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/data/_voiture/alcopa original/dates"
#
# directory_path = "/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/data/_voiture/alcopa original/flash"
# directory_path = "/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/data/_voiture/alcopa original/multilist"

# PATH = '/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/test/alcopa_sales/08'
PATH = '/Users/maximebeauger/Projects/PYTHON/alcopa_sales'
DB_PATH = PATH + '/alcopa_sales.db'
LOG_PATH = PATH + '/process_log.log'

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
        logging.info(f"Successfully extracted JSON data from {file_path}.")
        return json_data

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in extract_json_from_html: {e}")
        return None    

def insert_data(conn, json_data):
    cursor = conn.cursor()

    try:
        sale = json_data.get('sale', {})
        sale_id_number = sale.get('id')
        sale_date = datetime.now().strftime('%Y-%m-%d')
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
            # logging.info(f"Inserted product data for lot ID: {lot.get('lotId')}")

        conn.commit()

    except Exception as e:
        logging.error(f"Error inserting data: {e}")

def process_files_recursively(directory_path):
    conn = create_database(DB_PATH)

    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith('.html'):
                file_path = os.path.join(root, filename)
                logging.info(f"Processing file: {file_path}")
                json_data = extract_json_from_html(file_path)
                if json_data:
                    insert_data(conn, json_data)
                logging.info(f" --- ")

    conn.close()
    logging.info("Data processing completed.")


if __name__ == "__main__":
    # directory_path = "/path/to/html/files"
    process_files_recursively(directory_path)
    # process_files_in_directory(directory_path)
