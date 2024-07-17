# This code creates a Tkinter GUI for inputting a VIN or customer ID, selecting an Excel file, and generating a service reminder mail using OpenAI's GPT-4. The generated mail is displayed in the GUI and saved in the Excel file's column T.
# OpenAI Client: Sets up the API client.
# Mail Generation: Uses GPT-4 to create a service reminder mail based on customer details.
# Excel Update:
# Prompts user to select an Excel file.
# Finds the row matching the VIN or customer ID.
# Generates and displays mail.
# Saves mail content in column T of the Excel file.
# GUI Setup:
# Takes VIN or customer ID input.
# Button to select Excel file and generate mail.
# Displays mail in a scrollable text widget.
# Main Function: Runs the Tkinter main loop.






import os
import pandas as pd
from openai import OpenAI
from tkinter import Tk, filedialog, ttk, Text, Scrollbar, VERTICAL, RIGHT, Y, BOTH, Entry, Label, Button

# Initialize the OpenAI client with the provided API key
client = OpenAI(
    api_key="openai_key"  # Replace with your actual API key
)

# Function to generate the service reminder mail using OpenAI's GPT-4 model
def generate_service_reminder_mail(first_name, last_name, city, brand, model, dealer_assignment):
    prompt = f"""
    Write an automotive dealership service reminder mail for a service agent:
    - Customer Name: {first_name} {last_name}
    - City: {city}
    - Brand: {brand}
    - Model: {model}
    - Dealer Assignment: {dealer_assignment}
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful BMW Service assistant that always answers in BMW formal corporate language."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

# Function to update the existing Excel file with generated mail content
def update_excel_with_mail_content(vin_or_id):
    excel_file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if not excel_file_path:
        return

    df = pd.read_excel(excel_file_path, sheet_name=0)

    # Find the row matching the provided VIN or customer ID
    row = df[(df['vin'] == vin_or_id) | (df['customer_id'] == vin_or_id)]
    
    if row.empty:
        text_widget.delete(1.0, "end")
        text_widget.insert("end", "No matching VIN or customer ID found.")
        return

    # Extract required columns
    index = row.index[0]
    row = row.iloc[0]
    first_name = row['first_name']
    last_name = row['last_name']
    city = row['city']
    brand = row['brand']
    model = row['model']
    dealer_assignment = row['dealer_assignment']

    # Generate the mail content using OpenAI GPT-4
    mail_content = generate_service_reminder_mail(first_name, last_name, city, brand, model, dealer_assignment)
    
    # Display the generated mail content in the Tkinter Text widget
    text_widget.delete(1.0, "end")
    text_widget.insert("end", mail_content)
    
    # Update the DataFrame with the new mail content in column T
    df.at[index, 'mail_content'] = mail_content
    
    # Save the updated DataFrame back to the Excel file
    df.to_excel(excel_file_path, index=False)

def on_submit():
    vin_or_id = entry.get()
    update_excel_with_mail_content(vin_or_id)

# Main function to create the GUI application
def main():
    global text_widget, entry

    root = Tk()
    root.title("Automotive Service Reminder Mail Creator")
    root.configure(bg='#2e2e2e')

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TLabel', background='#2e2e2e', foreground='#ffffff', font=('Helvetica', 12))
    style.configure('TButton', background='#444444', foreground='#ffffff', font=('Helvetica', 12))
    style.map('TButton', background=[('active', '#666666')])

    label = ttk.Label(root, text="Enter VIN or Customer ID:")
    label.pack(pady=10)

    entry = Entry(root, font=('Helvetica', 12))
    entry.pack(pady=5)

    btn_update_excel = ttk.Button(root, text="Select Excel file and generate mail content", command=on_submit)
    btn_update_excel.pack(pady=5)

    text_frame = ttk.Frame(root)
    text_frame.pack(pady=10, padx=10, fill=BOTH, expand=True)

    scrollbar = Scrollbar(text_frame, orient=VERTICAL)
    scrollbar.pack(side=RIGHT, fill=Y)

    text_widget = Text(text_frame, wrap='word', yscrollcommand=scrollbar.set, background='#2e2e2e', foreground='#ffffff', font=('Helvetica', 12))
    text_widget.pack(fill=BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    root.mainloop()

if __name__ == "__main__":
    main()
