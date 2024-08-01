import os
from collections import OrderedDict
from flask import Flask, request, render_template, jsonify
import pandas as pd
from openai import OpenAI

# Initialize the OpenAI client with the provided API key
client = OpenAI(api_key="openai_api_key")  # Replace with your actual API key

app = Flask(__name__)
app.config['MAIL_FOLDER'] = 'mails'

def generate_service_reminder_mail(first_name, last_name, city, brand, model, dealer_assignment, formality, length, service_due_text, discount_text, insurance_text):
    formality_map = {
        'formell': 'formelle',
        'normal': 'normale',
        'informell': 'informelle'
    }

    length_map = {
        'kurz': 'kurze',
        'mittel lang': 'mittellange',
        'lang': 'lange'
    }

    formality_text = formality_map.get(formality, 'normal')
    length_text = length_map.get(length, 'mittel lang')

    prompt = f"""
    Schreibe eine {formality_text} und {length_text} Service-Erinnerungs-Mail für einen Kunden eines Autohauses. Schreibe sie im Fließtext und nicht in Aufzählungspunkten. Verwende die folgenden Informationen:
    - Kundenname: {first_name} {last_name}
    - Stadt: {city}
    - Marke: {brand}
    - Modell: {model}
    - Händlerzuweisung: {dealer_assignment}
    - Servicehinweis: {service_due_text}
    """

    if discount_text:
        prompt += f"\n- Folgender Rabatt kann dem Kunden angeboten werden: {discount_text}"

    if insurance_text:
        prompt += f"\n- Folgende Versicherung kann dem Kunden angeboten werden: {insurance_text}"
    
    print("OpenAI API prompt:", prompt)  # Print the prompt to the terminal

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful BMW Service assistant that always answers in BMW formal corporate language."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    vin_or_id = request.form['vin_or_id']
    formality = request.form.get('formality', 'normal')
    length = request.form.get('length', 'mittel lang')
    
    df = pd.read_excel(file)
    
    row = df[(df['vin'] == vin_or_id) | (df['customer_id'] == vin_or_id)]

    if row.empty:
        return jsonify({"error": "No matching VIN or customer ID found."}), 404

    row = row.iloc[0]
    first_name = row['first_name']
    last_name = row['last_name']
    city = row['city']
    brand = row['brand']
    model = row['model']
    dealer_assignment = row['dealer_assignment']

    sensors_due = [sensor.replace('sensor_', '').replace('_', ' ') for sensor in [
        'sensor_engine_oil', 'sensor_tire', 'sensor_break_front', 'sensor_break_back',
        'sensor_break_fluid', 'sensor_vehicle_check', 'sensor_inspection', 'sensor_drive_habits'
    ] if row[sensor] in [2, 3]]

    service_due_text = ", ".join(sensors_due)

    discount_text = "20% off" if row['lead_score_loyalty'] < 30 else ""
    insurance_text = "Repair Cost Insurance" if row['lead_score_profit'] > 40 else ""

    mail_content = generate_service_reminder_mail(first_name, last_name, city, brand, model, dealer_assignment, formality, length, service_due_text, discount_text, insurance_text)

    # Save the mail content to a text file named with the VIN
    vin = row['vin']
    mail_filepath = os.path.join(app.config['MAIL_FOLDER'], f"{vin}.txt")
    with open(mail_filepath, 'w') as mail_file:
        mail_file.write(mail_content)

    # Collect all row data for displaying and handle NaN values
    row_data = row.to_dict()
    row_data = {key: (value if pd.notna(value) else None) for key, value in row_data.items()}
    ordered_keys = [
        'vin', 'customer_id', 'first_name', 'last_name', 'customer_age', 'country', 
        'city', 'landkreis_verfügbares_einkommen', 'brand', 'model', 'car_age', 
        'mileage', 'mileage_year', 'dealer_assignment', 'dealer_assignment_status', 
        'lead_score_profit', 'lead_score_loyalty', 'customer_persona', 'sensor_engine_oil',
        'sensor_tire', 'sensor_break_front', 'sensor_break_back', 'sensor_break_fluid',
        'sensor_vehicle_check', 'sensor_inspection', 'sensor_drive_habits', 'last_service_date'
    ]
    ordered_row_data = OrderedDict((key, row_data.get(key)) for key in ordered_keys if key in row_data)

    response_data = {
        "mail_content": mail_content,
        "row_data": ordered_row_data,
        "loyalty_field_state": "green" if row['lead_score_loyalty'] < 30 else "red",
        "insurance_field_state": "green" if row['lead_score_profit'] > 40 else "red"
    }

    return jsonify(response_data)

if __name__ == "__main__":
    if not os.path.exists(app.config['MAIL_FOLDER']):
        os.makedirs(app.config['MAIL_FOLDER'])
    app.run(debug=True)
