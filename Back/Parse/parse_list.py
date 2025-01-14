import requests
from bs4 import BeautifulSoup

directory_path = "/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/test/alcopa_sales/sales/list_Vente de multisite du 28 novembre 2024 | Alcopa Auction.html"

# Загружаем содержимое HTML из файла
with open(directory_path, "r", encoding="utf-8") as file:
    html_content = file.read()

# Парсим HTML с помощью BeautifulSoup
# soup = BeautifulSoup(html_content, "lxml")
soup = BeautifulSoup(html_content, "html.parser"

# Ищем все ссылки на лоты
lot_links = []
for link in soup.find_all('a', href=True):
    href = link['href']
    # Проверяем, что ссылка ведет на страницу лота (обычно содержит "/lot/")
    if "/lot/" in href:
        full_url = "https://www.alcopa-auction.fr" + href
        lot_links.append(full_url)

# Выводим все найденные ссылки
print("Найденные ссылки на лоты:")
for link in lot_links:
    print(link)
