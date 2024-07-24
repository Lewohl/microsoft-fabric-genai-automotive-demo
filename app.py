import os
import logging
from collections import OrderedDict
from flask import Flask, request, render_template, jsonify
import pandas as pd
from openai import OpenAI
from werkzeug.utils import secure_filename

# Initialize the OpenAI client with the provided API key
client = OpenAI(api_key="api_key_here")  # Replace with your actual API key

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

logging.basicConfig(level=logging.DEBUG)

def generate_service_reminder_mail(first_name, last_name, city, brand, model, dealer_assignment):
    prompt = f"""
    Write an automotive dealership service reminder mail for a service agent. Write it in text and not bulletpoints. Use the following information:
    - Customer Name: {first_name} {last_name}
    - City: {city}
    - Brand: {brand}
    - Model: {model}
    - Dealer Assignment: {dealer_assignment}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful BMW Service assistant that always answers in BMW formal corporate language."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.5,
    )
    logging.debug('OpenAI API response: %s', response)
    return response.choices[0].message.content.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.debug('Received file upload request')
    if 'file' not in request.files:
        logging.error('No file part')
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        logging.error('No selected file')
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    logging.debug(f'Saving file to {filepath}')
    file.save(filepath)

    vin_or_id = request.form['vin_or_id']
    logging.debug(f'Processing VIN or Customer ID: {vin_or_id}')
    df = pd.read_excel(filepath, sheet_name=0)
    
    row = df[(df['vin'] == vin_or_id) | (df['customer_id'] == vin_or_id)]
    
    if row.empty:
        logging.error('No matching VIN or customer ID found')
        return jsonify({"error": "No matching VIN or customer ID found."}), 404

    index = row.index[0]
    row = row.iloc[0]
    first_name = row['first_name']
    last_name = row['last_name']
    city = row['city']
    brand = row['brand']
    model = row['model']
    dealer_assignment = row['dealer_assignment']

    mail_content = generate_service_reminder_mail(first_name, last_name, city, brand, model, dealer_assignment)

    # Ensure the 'mail_content' column is of type str
    df['mail_content'] = df['mail_content'].astype(str)
    logging.debug('Updating mail content in DataFrame')

    df.at[index, 'mail_content'] = mail_content
    df.to_excel(filepath, index=False)

    # Collect all row data for displaying and handle NaN values
    row_data = row.to_dict()
    row_data = {key: (value if pd.notna(value) else None) for key, value in row_data.items()}
    ordered_keys = [
        'vin', 'customer_id', 'first_name', 'last_name', 'customer_age', 'country', 
        'city', 'landkreis_verfügbares_einkommen', 'brand', 'model', 'car_age', 
        'mileage', 'mileage_year', 'dealer_assignment', 'dealer_assignment_status', 
        'lead_score_profit', 'lead_score_loyalty', 'customer_persona', 'Unnamed: 18', 
        'mail_content'
    ]
    ordered_row_data = OrderedDict((key, row_data.get(key)) for key in ordered_keys if key in row_data)
    
    logging.debug('Returning mail content and row data')
    response_data = {"mail_content": mail_content, "row_data": ordered_row_data}
    logging.debug('Response data: %s', response_data)

    return jsonify(response_data)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
