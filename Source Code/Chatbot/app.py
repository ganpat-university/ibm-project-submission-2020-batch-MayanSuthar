from flask import Flask, render_template, request, redirect
import os
import time
from cryptography.fernet import Fernet
import mysql.connector
import re

# Encryption key generation
def generate_key():
    return Fernet.generate_key()

# Encrypt data
def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

# Decrypt data
def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

# Function to save encrypted chat history
def save_chat_history(chat_history, key, history_file):
    encrypted_history = encrypt_data(chat_history, key)
    with open(history_file, 'wb') as f:
        f.write(encrypted_history.encode())

# Function to load encrypted chat history
def load_chat_history(key, history_file):
    if not os.path.exists(history_file):
        return ''
    with open(history_file, 'rb') as f:
        encrypted_history = f.read().decode()
        return decrypt_data(encrypted_history, key)

def fetch_data_from_database(keyword):
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mayan",
        database="cv"
    )

    cursor = connection.cursor()

    query = f"SELECT * FROM user_data WHERE act_name LIKE '%{keyword}%'"
    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result

name = 'BOT'
role = 'Resume analyzer'
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
    Forward them to the website for more information.
    YOU ARE NOT AN AI MODEL!
"""

explicit_input = ""
cwd = os.getcwd()
i = 1

while os.path.exists(os.path.join(cwd, f'chat_history{i}.txt')):
    i += 1

history_file = os.path.join(cwd, f'chat_history{i}.txt')
encryption_key = generate_key()  # Generate encryption key
chat_history = load_chat_history(encryption_key, history_file)  # Load chat history

# Create a Flask web application
app = Flask(__name__)

def extract_keywords(user_input):
    # Use regex to extract words from user input
    keywords = re.findall(r'\b\w+\b', user_input)
    return keywords

def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
    keywords = extract_keywords(user_input)
    if keywords:
        # Fetch data from database based on keywords
        data_from_db = fetch_data_from_database(keywords)
        if data_from_db:
            # Return database result as bot response
            return str(data_from_db)
    # Placeholder response if no keyword found or no data in database
    return "Sorry, I couldn't find any relevant information."

def chat(user_input):
    global chat_history, name
    current_day = time.strftime("%d/%m", time.localtime())
    current_time = time.strftime("%H:%M:%S", time.localtime())
    chat_history += f'\nUser: {user_input}\n'
    data_from_db = None
    keywords = extract_keywords(user_input)
    for keyword in keywords:
        # Fetch data from database based on keyword
        data_from_db = fetch_data_from_database(keyword)
        if data_from_db:
            # Format database result as a table
            table = "<table border='1'>"
            table += "<tr><th>ID</th><th>Name</th><th>city</th></tr>"
            for row in data_from_db:
                table += f"<tr><td>{row[0]}</td><td>{row[14]}</td><td>{row[8]}</td></tr>"
            table += "</table>"
            response = table
            break  # Exit loop if data found
    else:
        # Placeholder response if no keyword found or no data in database
        response = "Sorry, I couldn't find any relevant information."
    chatgpt_raw_output = response.replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    save_chat_history(chat_history, encryption_key, history_file)  # Save encrypted chat history
    with open(history_file, 'a') as f:
        f.write('\n'+ current_day+ ' '+ current_time+ ' User: ' +user_input +' \n' + current_day+ ' ' + current_time+  ' ' +  chatgpt_output + '\n')
    return chatgpt_raw_output


# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)

# Define app routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
# Function for the bot response
def get_bot_response():
    userText = request.args.get('msg')
    return str(get_response(userText))

@app.route('/refresh')
def refresh():
    time.sleep(600) # Wait for 10 minutes
    return redirect('/refresh')

# Run the Flask app
if __name__ == "__main__":
    app.run()
