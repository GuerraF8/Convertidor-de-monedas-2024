# backend_conversion/app.py

from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URL del Servicio de Conversión
EXCHANGE_RATE_SERVICE_URL = os.getenv('EXCHANGE_RATE_SERVICE_URL', 'http://backend_rates:5000')

@app.route('/api/convert', methods=['POST'])
def convert_currency():
    data = request.get_json()
    from_currency = data.get('from_currency', '').upper()
    to_currency = data.get('to_currency', '').upper()
    amount = data.get('amount', 0.0)
    
    if not from_currency or not to_currency or not amount:
        return jsonify({'error': 'Parámetros incompletos.'}), 400

    if from_currency == to_currency:
        return jsonify({
            'original_amount': float(amount),
            'converted_amount': float(amount),
            'exchange_rate': 1.0,
            'from_currency': from_currency,
            'to_currency': to_currency
        })
    
    try:
        # Si la moneda de origen es USD
        if from_currency == 'USD':
            response = requests.get(f"{EXCHANGE_RATE_SERVICE_URL}/rates?from=USD&to={to_currency}")
            rate_data = response.json()
            if 'rate' in rate_data and rate_data['rate'] != 0:
                rate = rate_data['rate']
            else:
                return jsonify({'error': 'No se pudo obtener la tasa de cambio o es cero.'}), 400
        # Si la moneda de destino es USD
        elif to_currency == 'USD':
            response = requests.get(f"{EXCHANGE_RATE_SERVICE_URL}/rates?from=USD&to={from_currency}")
            rate_data = response.json()
            if 'rate' in rate_data and rate_data['rate'] != 0:
                rate = 1 / rate_data['rate']
            else:
                return jsonify({'error': 'No se pudo obtener la tasa de cambio o es cero.'}), 400
        # Si ninguna de las monedas es USD
        else:
            # Obtener tasa de from_currency a USD
            response_from = requests.get(f"{EXCHANGE_RATE_SERVICE_URL}/rates?from=USD&to={from_currency}")
            rate_data_from = response_from.json()
            if 'rate' in rate_data_from and rate_data_from['rate'] != 0:
                rate_from = rate_data_from['rate']
            else:
                return jsonify({'error': f'No se pudo obtener la tasa de USD a {from_currency} o es cero.'}), 400
                
            # Obtener tasa de USD a to_currency
            response_to = requests.get(f"{EXCHANGE_RATE_SERVICE_URL}/rates?from=USD&to={to_currency}")
            rate_data_to = response_to.json()
            if 'rate' in rate_data_to and rate_data_to['rate'] != 0:
                rate_to = rate_data_to['rate']
            else:
                return jsonify({'error': f'No se pudo obtener la tasa de USD a {to_currency} o es cero.'}), 400
                
            # Calcular la tasa de from_currency a to_currency
            rate = rate_to / rate_from
        
        converted_amount = float(amount) * rate
        return jsonify({
            'original_amount': float(amount),
            'converted_amount': round(converted_amount, 6),
            'exchange_rate': round(rate, 8),
            'from_currency': from_currency,
            'to_currency': to_currency
        })
    except Exception as e:
        print(e)
        return jsonify({'error': 'Error en la conversión.'}), 500

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    try:
        response = requests.get(f"{EXCHANGE_RATE_SERVICE_URL}/currencies")
        response.raise_for_status()
        currencies = response.json()
        return jsonify(currencies)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener las monedas: {e}")
        return jsonify({'error': 'Error al obtener las monedas.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)