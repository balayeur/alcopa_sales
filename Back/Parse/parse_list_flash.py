# File path: app.py
# import sqlite3
import requests
from flask import Flask, render_template
from bs4 import BeautifulSoup

# Step 1: Fetch HTML content from the webpage
def fetch_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for HTTP issues
    return response.text

# Step 2: Parse HTML to extract auction data
def parse_html(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    auctions = []

    auction_items = soup.select('div.auction-card')  # Update selector based on webpage structure
    for item in auction_items:
        print(item)
        auction_type = item.find('span', class_='auction-type').text.strip()
        lots = item.find('span', class_='lots').text.strip()
        description = item.find('div', class_='description').text.strip()
        countdown = item.find('div', class_='countdown').text.strip()
        auctions.append((auction_type, lots, description, countdown))

    return auctions

# # Step 3: Save data to SQLite database
# def save_to_database(auctions, db_path='alcopa_sales.db'):
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
    
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS auctions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             auction_type TEXT,
#             lots TEXT,
#             description TEXT,
#             countdown TEXT
#         )
#     ''')
#     cursor.executemany('INSERT INTO auctions (auction_type, lots, description, countdown) VALUES (?, ?, ?, ?)', auctions)
#     conn.commit()
#     conn.close()

# Step 4: Flask app to render the table
app = Flask(__name__)

# @app.route('/')
# def index():
#     conn = sqlite3.connect('alcopa_sales.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT auction_type, lots, description, countdown FROM auctions')
#     data = cursor.fetchall()
#     conn.close()
#     return render_template('table.html', data=data)

if __name__ == '__main__':
    # URL of the webpage
    url = 'https://www.alcopa-auction.fr/salle-de-vente-web'

    # Fetch HTML, parse data, and save to DB
    # html_content = fetch_html(url)
    # auctions = parse_html(html_content)

    # Parse HTML and save data to DB
    html_file = '/Users/maximebeauger/Downloads/liste_flash.html'  # Replace with actual file path
    # with open(html_file, 'r', encoding='utf-8') as file:
    #     content = file.read()
    auctions = parse_html(html_file)

    print(auctions)
    # save_to_database(auctions)

    # Start Flask app
    # app.run(debug=True)
