import re
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime
import getpass

import urllib

app = Flask(__name__)

USER_NAME = getpass.getuser()
print("USER_NAME = " + USER_NAME)

# Получить текущий рабочий каталог
current_directory = os.getcwd()
# Вывести текущий каталог в консоль
# current_directory = "/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/test/alcopa_sales/08"
current_directory = "/Users/" + USER_NAME + "/Projects/PYTHON/alcopa_sales"

print(f"Info:: Текущий каталог: {current_directory}")

# DB_PATH = '/Users/maximebeauger/Dropbox/SHARED/workspace/PYTHON/LotScanner/test/alcopa_sales/alcopa_sales06.db'
# DB_PATH = 'alcopa_sales0.db'

# DB_PATH = "/Users/dionis/Dropbox/SHARED/workspace/PYTHON/ALCOPA_common/alcopa_sales.db"
# DB_PATH = current_directory + '/alcopa_sales.db'
DB_PATH = current_directory + '/_Files/bdd/alcopa_sales.db'
DB_PATH = '/Users/dionis/Project/Python/alcopa_sales/_Files/bdd/alcopa_sales.db'

print(f"Info:: BDD path: {DB_PATH}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/')
def index():
    conn = get_db_connection()
    sales = conn.execute("""
        SELECT id, id_number, date, isCorrectionMode, isEnded, infocom, title, type, room
        FROM Sales
        ORDER BY date DESC
    """).fetchall()
    conn.close()
    return render_template('index.html', sales=sales)



@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Product WHERE sale_id = ?", (sale_id,))
    conn.execute("DELETE FROM Sales WHERE id = ?", (sale_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))



@app.route('/sales/<int:sale_id>')
def sale_details(sale_id):
    conn = get_db_connection()
    sale = conn.execute("""
        SELECT id_number, date, isCorrectionMode, isEnded, infocom, title, type, room
        FROM Sales
        WHERE id = ?
    """, (sale_id,)).fetchone()

    products = conn.execute("""
        SELECT p.model, p.name, p.lotId, p.openingBid, p.mainImgUrl, p.detailsUrl, 
               p.highestBidValue, p.lotNumber, p.energy, p.mileage, p.rollout, p.gearbox, 
               p.isActive, p.type, p.decision, p.extraRound,
               (SELECT COUNT(*) 
                FROM Product AS other
                WHERE other.mileage = p.mileage
                  AND other.rollout = p.rollout
                  AND other.sale_id != ?) AS mileage_count
        FROM Product AS p
        WHERE p.sale_id = ?
    """, (sale_id, sale_id)).fetchall()

    # products = conn.execute("""
    #     SELECT model, name, lotId, openingBid, mainImgUrl, detailsUrl, highestBidValue, lotNumber,
    #            energy, mileage, rollout, gearbox, isActive, type, decision, extraRound
    #     FROM Product
    #     WHERE sale_id = ?
    # """, (sale_id,)).fetchall()
    
    conn.close()
    return render_template('products.html', sale=sale, products=products)



# # страницу для поиска по всей базе данных
# @app.route('/search_all', methods=['GET', 'POST'])
# def search():
#     conn = get_db_connection()

#     # Извлекаем уникальные значения для выпадающих списков
#     filters = {
#         "energy": conn.execute("SELECT DISTINCT energy FROM Product").fetchall(),
#         "gearbox": conn.execute("SELECT DISTINCT gearbox FROM Product").fetchall(),
#         "type": conn.execute("SELECT DISTINCT type FROM Product").fetchall(),
#         "decision": conn.execute("SELECT DISTINCT decision FROM Product").fetchall(),
#         "room": conn.execute("SELECT DISTINCT room FROM Sales").fetchall(),
#     }

#     results = []
#     if request.method == 'POST':
#         # Читаем фильтры из запроса
#         filters_selected = {
#             "model": request.form.get("model"),
#             "name": request.form.get("name"),
#             "energy": request.form.get("energy"),
#             "gearbox": request.form.get("gearbox"),
#             "type": request.form.get("type"),
#             "decision": request.form.get("decision"),
#             "room": request.form.get("room"),
#         }

#         # Формируем SQL-запрос с динамическими условиями
#         conditions = []
#         parameters = []
        
#         for field, value in filters_selected.items():
#             if value:
#                 if field in ["model", "name"]:  # Поиск по текстовым полям
#                     conditions.append(f"{field} LIKE ?")
#                     parameters.append(f"%{value}%")
#                 else:  # Поиск по точному совпадению
#                     conditions.append(f"{field} = ?")
#                     parameters.append(value)

        
#         query = """
#             SELECT Product.model, Product.name, Product.mileage, Product.rollout,
#                 Product.openingBid, Product.highestBidValue, Product.lotId,
#                 Product.mainImgUrl, Product.detailsUrl, Product.energy,
#                 Product.gearbox, Product.type, Product.decision, Sales.id_number,
#                 Sales.room
#             FROM Product
#             JOIN Sales ON Product.sale_id = Sales.id

#         """
#         if conditions:
#             query += " WHERE " + " AND ".join(conditions)

#         results = conn.execute(query, parameters).fetchall()

#     conn.close()
#     return render_template('search_all.html', filters=filters, results=results)


# 🧪 Usage examples
# Search by rollout only:
# GET /search_all/rollout/2023-06-15
# Search by mileage + rollout:
# GET /search_all/150000/2022-01-01
# Combination with form filters still works normally.
@app.route('/search_all', methods=['GET', 'POST'])
@app.route('/search_all/<mileage>', methods=['GET', 'POST'])
@app.route('/search_all/<mileage>/<rollout>', methods=['GET', 'POST'])
@app.route('/search_all/rollout/<rollout>', methods=['GET', 'POST'])
@app.route('/search_all/rollout/<rollout>/<mileage>', methods=['GET', 'POST'])
def search(mileage=None, rollout=None):
    conn = get_db_connection()

    # Извлекаем уникальные значения для фильтров
    filters = {
        "energy": [row[0] for row in conn.execute("SELECT DISTINCT energy FROM Product").fetchall()],
        "gearbox": [row[0] for row in conn.execute("SELECT DISTINCT gearbox FROM Product").fetchall()],
        "type": [row[0] for row in conn.execute("SELECT DISTINCT type FROM Product").fetchall()],
        "decision": [row[0] for row in conn.execute("SELECT DISTINCT decision FROM Product").fetchall()],
        "room": [row[0] for row in conn.execute("SELECT DISTINCT room FROM Sales").fetchall()],
    }

    results = {}

    # Очистка пробега (удаляем пробелы и "km")
    def clean_mileage(value):
        if value:
            return re.sub(r"[^\d]", "", urllib.parse.unquote(value))
        return None

    mileage_filter = clean_mileage(mileage)
    # rollout date passed via URL (no cleaning needed, keep raw string)
    rollout_filter = urllib.parse.unquote(rollout) if rollout else None

    if request.method == 'POST' or mileage_filter:
        filters_selected = {
            "model": request.form.get("model") or None,
            "name": request.form.get("name") or None,
            "energy": request.form.get("energy") or None,  # ✅ Обрабатываем "Все" как None
            "gearbox": request.form.get("gearbox") or None,
            "type": request.form.get("type") or None,
            "decision": request.form.get("decision") or None,
            "room": request.form.get("room") or None,
            "mileage_exact": mileage_filter if mileage_filter else None,
            "mileage_min": clean_mileage(request.form.get("mileage_min")),
            "mileage_max": clean_mileage(request.form.get("mileage_max")),
            "rollout_exact": rollout_filter if rollout_filter else None,
            "rollout_min": request.form.get("rollout_min") or None,
            "rollout_max": request.form.get("rollout_max") or None,
        }

        conditions = []
        parameters = []

        for field, value in filters_selected.items():
            if value:
                if field in ["model", "name"]:
                    conditions.append(f"Product.{field} LIKE ?")
                    parameters.append(f"%{value}%")
                elif field == "mileage_exact":
                    conditions.append("CAST(REPLACE(REPLACE(Product.mileage, ' ', ''), 'km', '') AS INTEGER) = ?")
                    parameters.append(value)
                elif field in ["mileage_min", "mileage_max"]:
                    if field == "mileage_min":
                        conditions.append("CAST(REPLACE(REPLACE(Product.mileage, ' ', ''), 'km', '') AS INTEGER) >= ?")
                    else:
                        conditions.append("CAST(REPLACE(REPLACE(Product.mileage, ' ', ''), 'km', '') AS INTEGER) <= ?")
                    parameters.append(value)
                elif field == "rollout_exact":
                    conditions.append("Product.rollout = ?")
                    parameters.append(value)
                elif field in ["rollout_min", "rollout_max"]:
                    conditions.append(f"Product.rollout {'>=' if field == 'rollout_min' else '<='} ?")
                    parameters.append(value)
                elif field in ["energy", "gearbox", "type", "decision", "room"]:
                    conditions.append(f"Product.{field} = ?")
                    parameters.append(value)
                else:
                    conditions.append(f"Product.{field} = ?")
                    parameters.append(value)

        query = """
            SELECT Product.model, Product.name, Product.mileage, Product.rollout,
                   Product.openingBid, Product.highestBidValue, Product.mainImgUrl,
                   Product.detailsUrl, Product.energy, Product.gearbox, Product.type, 
                   Product.decision, Product.lotId, Sales.id_number, Sales.room, Sales.date
            FROM Product
            JOIN Sales ON Product.sale_id = Sales.id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        raw_results = conn.execute(query, parameters).fetchall()

        # Группируем автомобили по mileage + rollout
        for row in raw_results:
            # car_key = (row["model"], row["name"])
            # Для более точного группирования используем mileage + rollout, 
            # так как model + name могут быть одинаковыми для разных автомобилей
            car_key = (row["mileage"], row["rollout"])
            auction_info = {
                "lotNumber": row["lotId"],
                "openingBid": row["openingBid"],
                "highestBidValue": row["highestBidValue"],
                "decision": row["decision"],
                "date": row["date"],
                "id_number": row["id_number"],
                "room": row["room"],
                "sale_url": f"/auction/{row['id_number']}#lot-{row['lotId']}"
            }

            if car_key not in results:
                results[car_key] = {
                    "model": row["model"],
                    "name": row["name"],
                    "mileage": row["mileage"],
                    "rollout": row["rollout"],
                    "mainImgUrl": row["mainImgUrl"],
                    "detailsUrl": row["detailsUrl"],
                    "energy": row["energy"],
                    "gearbox": row["gearbox"],
                    "type": row["type"],
                    "decision": row["decision"],
                    "auctions": [auction_info]
                }
            else:
                results[car_key]["auctions"].append(auction_info)

        # Сортируем аукционы по убыванию даты (новые выше)
        for car in results.values():
            car["auctions"].sort(key=lambda x: x["date"], reverse=True)

    conn.close()
    return render_template('search_all.html', filters=filters, results=results,
                           mileage_filter=mileage_filter, rollout_filter=rollout_filter)


# страницу для отображения найденных записей
@app.route('/search-sales/<string:mileage>')
def search_sales(mileage):
    conn = get_db_connection()
    results = conn.execute("""
        SELECT p.model, p.name, p.lotNumber, p.mileage, p.openingBid, 
               p.highestBidValue, p.type, p.decision, s.date, s.room
        FROM Product p
        JOIN Sales s ON p.sale_id = s.id
        WHERE p.mileage = ?
        ORDER BY s.date DESC
    """, (mileage,)).fetchall()
    conn.close()
    return render_template('search_results.html', mileage=mileage, results=results)

# @app.route('/search-sales/<string:mileage>')
# def search_sales(mileage):
#     conn = get_db_connection()
#     sales = conn.execute("""
#         SELECT sale_id, model, name, openingBid, highestBidValue, lotNumber, energy, mileage, rollout, gearbox, isActive, type, decision
#         FROM Product
#         WHERE mileage = ?
#     """, (mileage,)).fetchall()
#     conn.close()

#     if not sales:
#         return render_template('search_results.html', sales=[], message="Записи не найдены.")

#     return render_template('search_results.html', sales=sales, message=None)



# Новый маршрут для получения данных о лоте
@app.route('/lot-details/<int:lot_id>')
def lot_details(lot_id):
    conn = get_db_connection()
    lot = conn.execute("""
        SELECT model, name, energy, mileage, rollout, gearbox, openingBid, mainImgUrl, detailsUrl,
               highestBidValue, lotNumber, isActive, type, decision, extraRound
        FROM Product
        WHERE lotId = ?
    """, (lot_id,)).fetchone()
    conn.close()

    if lot is None:
        return jsonify({"error": "Лот не найден"}), 404

    # Преобразуем данные в JSON
    lot_data = {
        "model": lot["model"],
        "name": lot["name"],
        "energy": lot["energy"],
        "mileage": lot["mileage"],
        "rollout": lot["rollout"],
        "gearbox": lot["gearbox"],
        "openingBid": lot["openingBid"],
        "mainImgUrl": lot["mainImgUrl"],
        "detailsUrl": lot["detailsUrl"],
        "highestBidValue": lot["highestBidValue"],
        "lotNumber": lot["lotNumber"],
        "isActive": lot["isActive"],
        "type": lot["type"],
        "decision": lot["decision"],
        "extraRound": lot["extraRound"]
    }
    return jsonify(lot_data)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=True, port=5000)  # Укажите желаемый порт, например 5001
