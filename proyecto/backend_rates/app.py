# backend_rates/app.py

from flask import Flask, request, jsonify
import requests
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
from flask_cors import CORS
import sys

app = Flask(__name__)
CORS(app)

# Asegurarnos de que el directorio 'data' existe
if not os.path.exists('data'):
    os.makedirs('data')

DATABASE = 'data/exchange_rates.db'
API_KEY = os.getenv('API_KEY')

if not API_KEY:
    print("Error: La clave API no está definida. Por favor, establece la variable de entorno API_KEY.")
    sys.exit(1)

def create_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rates
                 (currency_from TEXT, currency_to TEXT, rate REAL, updated_at TEXT)''')
    conn.commit()
    conn.close()

def update_rates():
    print(f"Actualizando tasas de cambio a las {datetime.now()}")
    base_url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'
    response = requests.get(base_url)
    data = response.json()
    if data and data['result'] == 'success':
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('DELETE FROM rates')
        base_currency = data['base_code']
        rates = data['conversion_rates']
        updated_at = data['time_last_update_utc']
        for currency, rate in rates.items():
            c.execute('INSERT INTO rates (currency_from, currency_to, rate, updated_at) VALUES (?, ?, ?, ?)',
                      (base_currency, currency, rate, updated_at))
        conn.commit()
        conn.close()
    else:
        print("No se pudieron obtener las tasas de cambio.")
        print(f"Error: {data.get('error-type', 'Desconocido')}")

@app.route('/rates', methods=['GET'])
def get_rates():
    currency_from = request.args.get('from', 'USD').upper()
    currency_to = request.args.get('to')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if currency_to:
        c.execute('SELECT rate FROM rates WHERE currency_from=? AND currency_to=?',
                  (currency_from, currency_to.upper()))
        result = c.fetchone()
        if result:
            rate = result[0]
            conn.close()
            return jsonify({
                'currency_from': currency_from,
                'currency_to': currency_to.upper(),
                'rate': rate
            })
        else:
            conn.close()
            return jsonify({'error': 'Tasa de cambio no encontrada.'}), 404
    else:
        c.execute('SELECT currency_to, rate FROM rates WHERE currency_from=?', (currency_from,))
        rates = c.fetchall()
        conn.close()
        rates_list = []
        for r in rates:
            rates_list.append({
                'currency_from': currency_from,
                'currency_to': r[0],
                'rate': r[1]
            })
        return jsonify(rates_list)

@app.route('/currencies', methods=['GET'])
def get_currencies():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT DISTINCT currency_to FROM rates')
    currencies = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(currencies)

if __name__ == '__main__':
    create_db()
    update_rates()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_rates, trigger="interval", hours=1)
    scheduler.start()
    try:
        app.run(host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        pass