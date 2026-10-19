from flask import Flask, render_template, request, jsonify
import sqlite3
import config
from database import get_db_connection, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

init_db()

@app.route('/')
def index():
    return render_template('index.html')
# "<h1>Bienvenido a Legacy OrderHub API v1.0</h1><p>Estado del sistema: Producción con Deuda Técnica</p>"

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"[LOG LEGADO]: Ejecutando consulta SQL sin sanitizar: {query}")
    
    try:
        user = cursor.execute(query).fetchone()
        conn.close()
        if user:
            return jsonify({"status": "success", "user": dict(user)}), 200
        return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401
    except Exception as e:
        return jsonify({"status": "error", "exception": str(e)}), 500

@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    conn = get_db_connection()
    cursor = conn.cursor()

    product = cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404

    if product['stock'] < quantity:
        conn.close()
        return jsonify({"error": "Stock insuficiente"}), 400

    total = product['price'] * quantity

    cursor.execute(
        "INSERT INTO orders (user_id, product_id, quantity, total, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, product_id, quantity, total, 'PENDING')
    )
    order_id = cursor.lastrowid

    new_stock = product['stock'] - quantity
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
    conn.commit()
    conn.close()

    print(f"[LOG LEGADO]: Notificando al servicio de correos para la orden ID: {order_id}...")

    return jsonify({
        "message": "Orden creada con éxito",
        "order_id": order_id,
        "total": total
    }), 201

@app.route('/get_all_orders_legacy', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    
    result = [dict(o) for o in orders]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)