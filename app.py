import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Necesario para permitir llamadas desde el frontend

app = Flask(__name__)
# Habilita CORS para permitir llamadas desde cualquier origen (tu HTML)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Constante para el cálculo del prorrateo de la cuota fija
DAYS_IN_MONTH_AVG = 30.42

# Nombre del archivo JSON que contiene las tarifas
NOMBRE_ARCHIVO = "data/tarifas.json"

def cargar_tarifas_completas(nombre_fichero):
    """
    Carga el contenido de un archivo JSON en un diccionario de Python.
    """
    try:
        # 1. Abrir el fichero en modo lectura ('r')
        # La instrucción 'with' asegura que el fichero se cierra automáticamente.
        with open(nombre_fichero, 'r', encoding='utf-8') as archivo:
            # 2. Usar json.load() para leer directamente desde el objeto archivo
            datos = json.load(archivo)
            print(f"✅ Archivo '{nombre_fichero}' cargado exitosamente.")
            return datos
            
    except FileNotFoundError:
        print(f"❌ ERROR: El archivo '{nombre_fichero}' no se encontró en la ruta: {os.getcwd()}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: El archivo '{nombre_fichero}' no es un JSON válido. Error: {e}")
        return None

# ----------------------------------------------------
# 📌 ENDPOINT: OBTENER DETALLE POR ID
# RUTA: /tarifas/<tariff_id>
# ----------------------------------------------------
@app.route('/api/tarifas/<tariff_id>', methods=['GET'])
def obtener_detalle_tarifa(tariff_id):
    """
    Busca una tarifa por su ID y devuelve sus detalles completos.
    """
    # Cargar los datos completos
    datos_completos = cargar_tarifas_completas(NOMBRE_ARCHIVO)
    
    # 1. Manejar el error de carga de datos (si el archivo JSON falla)
    if datos_completos is None:
        return jsonify({
            "error": "Error interno del servidor",
            "message": "No se pudieron cargar los datos de las tarifas."
        }), 500
        
    perfiles = datos_completos.get('tariff_profiles', [])

    # 2. Buscar la tarifa por su ID (uso de expresión generadora 'next')
    tarifa_encontrada = next(
        (t for t in perfiles if t.get('tariff_id') == tariff_id), 
        None
    )
    
    # 3. Construir la respuesta
    if tarifa_encontrada:
        company = tarifa_encontrada.get('company', 'N/D')
        name = tarifa_encontrada.get('profile', 'Tarifa Desconocida')
        
        respuesta = {
            # Esto lo usa tu frontend para la descripción
            "description": f"{company} - {name}", 
            # Esto son los datos que necesita el frontend para el cálculo
            "details": tarifa_encontrada 
        }
        return jsonify(respuesta), 200
    else:
        # Respuesta 404
        # 🚨 DEBUGGING: Imprime la ID que no se encontró para confirmar
        print(f"DEBUG: No se encontró tarifa con ID: '{tariff_id}'")
        return jsonify({
            "error": "No encontrado", 
            "message": f"No se encontró ninguna tarifa con el ID: {tariff_id}"
        }), 404
        
@app.route('/api/general_costs')
def obtener_parametros():
    """
    Endpoint que devuelve un JSON con los parámetros generales
    """
    # 1. Cargar los datos completos
    datos_completos = cargar_tarifas_completas(NOMBRE_ARCHIVO)
    
    if datos_completos is None:
        # ⭐️ CORRECCIÓN CLAVE: Devolver un JSON de error y el código HTTP 500
        print("❌ Fallo en la carga de datos. Devolviendo error 500 al cliente.")
        return jsonify({"error": "No se pudieron cargar los datos de las tarifas. Verifique el archivo JSON y la ruta."}), 500
        
    params = datos_completos.get('general_costs', [])
    
    # 3. Devolver la lista como un JSON (Código 200 OK)
    return jsonify(params)

@app.route('/api/tarifas', methods=['GET'])
def obtener_resumen_tarifas():
    """
    Endpoint que devuelve un JSON con el ID, la compañía y el perfil de cada tarifa.
    """
    # 1. Cargar los datos completos
    datos_completos = cargar_tarifas_completas(NOMBRE_ARCHIVO)
    
    if datos_completos is None:
        # ⭐️ CORRECCIÓN CLAVE: Devolver un JSON de error y el código HTTP 500
        print("❌ Fallo en la carga de datos. Devolviendo error 500 al cliente.")
        return jsonify({"error": "No se pudieron cargar los datos de las tarifas. Verifique el archivo JSON y la ruta."}), 500
        
    perfiles = datos_completos.get('tariff_profiles', [])
    
    # 2. Procesar los datos para obtener el resumen solicitado
    resumen_tarifas = []
    for tarifa in perfiles:
        if all(key in tarifa for key in ['tariff_id', 'company', 'profile']):
            resumen_tarifas.append({
                "id": tarifa['tariff_id'],
                "company": tarifa['company'],
                "name": tarifa['profile']
            })
            
    # 3. Devolver la lista como un JSON (Código 200 OK)
    return jsonify(resumen_tarifas)

@app.route('/api/calculate', methods=['POST'])
def calculate_bill():
    """
    Endpoint que recibe los datos de la factura y calcula el importe total
    y los desgloses, devolviendo el resultado en formato JSON.
    """
    try:
        data = request.json

        # 1. Recolección y saneamiento de datos (convertir a float y usar 0.0 como fallback)
        billing_days = float(data.get('billingDays', 30.0))
        meter_rental_daily = float(data.get('meterRentalDaily', 0.0))
        fixed_monthly_fee = float(data.get('fixedMonthlyFee', 0.0))

        # Potencia
        contracted_power_p1 = float(data.get('contractedPowerP1', 0.0))
        power_price_daily_p1 = float(data.get('powerPriceDailyP1', 0.0))
        contracted_power_p2 = float(data.get('contractedPowerP2', 0.0))
        power_price_daily_p2 = float(data.get('powerPriceDailyP2', 0.0))

        # Consumo y Precios
        consumption_punta = float(data.get('consumptionPunta', 0.0))
        price_punta = float(data.get('pricePunta', 0.0))
        consumption_llano = float(data.get('consumptionLlano', 0.0))
        price_llano = float(data.get('priceLlano', 0.0))
        consumption_valle = float(data.get('consumptionValle', 0.0))
        price_valle = float(data.get('priceValle', 0.0))

        # Descuentos, Cargos e Impuestos (las tasas se dividen por 100 para obtener decimales)
        social_bono_discount_rate = float(data.get('socialBonoDiscountRate', 0.0)) / 100
        social_bono_financing_rate = float(data.get('socialBonoFinancingRate', 0.0))
        electricity_tax_rate = float(data.get('electricityTaxRate', 0.0)) / 100
        vat_rate = float(data.get('vatRate', 0.0)) / 100

        # --- CÁLCULOS PRINCIPALES (Logica migrada de JS a Python) ---

        # 2. Cálculo del Término de Potencia (Fijo - P1 y P2)
        power_term_p1 = contracted_power_p1 * power_price_daily_p1 * billing_days
        power_term_p2 = contracted_power_p2 * power_price_daily_p2 * billing_days
        power_term = power_term_p1 + power_term_p2

        # 3. Otros Costes Fijos (Alquiler + Cuota Fija Adicional)
        meter_rental_term = meter_rental_daily * billing_days
        prorated_fixed_fee = fixed_monthly_fee * (billing_days / DAYS_IN_MONTH_AVG)
        fixed_charges = power_term + meter_rental_term + prorated_fixed_fee

        # 4. Cálculo del Término de Energía (Variable - P1, P2 y P3)
        cost_punta = consumption_punta * price_punta
        cost_llano = consumption_llano * price_llano
        cost_valle = consumption_valle * price_valle

        energy_term = cost_punta + cost_llano + cost_valle
        total_consumption = consumption_punta + consumption_llano + consumption_valle

        # 5. Coste de Financiación del Bono Social (basado en consumo)
        social_bono_financing_cost = total_consumption * social_bono_financing_rate

        # 6. Base para Descuento
        # Se aplica sobre Potencia + Energía + Otros Fijos
        base_for_discount = fixed_charges + energy_term

        # 7. Descuento Bono Social
        social_bono_discount = base_for_discount * social_bono_discount_rate

        # 8. Base Imponible (Fijos + Energía + Financiación - Descuento)
        base_imponible = (fixed_charges + energy_term + social_bono_financing_cost) - social_bono_discount

        # 9. Impuesto Electricidad (IE)
        electricity_tax = base_imponible * electricity_tax_rate
        subtotal_tax_base = base_imponible + electricity_tax

        # 10. IVA/IGIC
        vat = subtotal_tax_base * vat_rate

        # 11. TOTAL
        total_bill = subtotal_tax_base + vat

        # 12. Devolver resultados estructurados
        results = {
            'totalBill': total_bill,
            'billingDays': billing_days,
            'totalConsumption': total_consumption,
            'powerTermP1': power_term_p1,
            'powerTermP2': power_term_p2,
            'powerTerm': power_term,
            'meterRentalTerm': meter_rental_term,
            'proratedFixedFee': prorated_fixed_fee,
            'fixedCharges': fixed_charges,
            'costPunta': cost_punta,
            'costLlano': cost_llano,
            'costValle': cost_valle,
            'energyTerm': energy_term,
            'socialBonoFinancingCost': social_bono_financing_cost,
            'socialBonoDiscount': social_bono_discount,
            'baseImponible': base_imponible,
            'electricityTax': electricity_tax,
            'subtotalTaxBase': subtotal_tax_base,
            'vat': vat,
        }

        return jsonify(results)

    except Exception as e:
        # Manejo de errores genérico en caso de que algo falle
        app.logger.error(f"Error en el cálculo: {e}")
        return jsonify({"error": "Error interno del servidor en el cálculo", "details": str(e)}), 500

if __name__ == '__main__':
    # Configuración de puerto para Render (puede ser necesario)
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)