import os
import flask
from flask import Flask, render_template, request, redirect, url_for
import requests
import google.generativeai as genai
from main import questions_and_answers
import datetime

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyA8KWyW2zNBXzTJAKKam_Xz2PZDNtml7mY"
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key

# Initialize Gemini model
try:
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    model = None
    print(f"Error initializing Gemini model: {e}")

def get_exchange_rate():
    try:
        # Use an API to get real-time exchange rate
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        data = response.json()
        return data['rates']['INR']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return 83.5  # Fallback to approximate rate if API fails

def get_answer(user_input):
    # First, check predefined Q&A
    for qa in questions_and_answers:
        if user_input.lower() in qa["question"].lower():
            answer = qa["answer"]
            # Handle dynamic answers (e.g., time or date)
            if callable(answer):
                return answer()
            return answer
   
    # If not in predefined Q&A, use Gemini
    if model:
        try:
            response = model.generate_content(user_input)
            return response.text
        except Exception as e:
            return f"Gemini error: {str(e)}"
   
    return "Sorry, I don't have an answer to that question."

def get_crypto_price(crypto_name):
    try:
        # CoinGecko API URL
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_name.lower()}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        if crypto_name.lower() in data:
            price = data[crypto_name.lower()]["usd"]
            return price, f"The current price of {crypto_name.capitalize()} is ${price:.2f} USD."
        else:
            return None, f"Sorry, I couldn't find the price for {crypto_name}. Please check the name and try again."
    except Exception as e:
        return None, "I'm having trouble fetching the price right now. Please try again later."

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/index')
def indexx():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['user_input']
   
    if "price of" in user_input.lower():
        crypto_name = user_input.lower().replace("price of", "").strip()
        price, answer = get_crypto_price(crypto_name)
        exchange_rate = get_exchange_rate()
        return render_template('index.html', 
                               user_input=user_input, 
                               answer=answer, 
                               price=price, 
                               exchange_rate=exchange_rate)
    else:
        answer = get_answer(user_input)
        return render_template('index.html', user_input=user_input, answer=answer)

@app.route('/convert',
 methods=['POST'])
def convert():
    price = float(request.form['price'])
    exchange_rate = float(request.form['exchange_rate'])
    direction = request.form['direction']

    if direction == 'usd_to_inr':
        converted_price = price * exchange_rate
        answer = f"${price:.2f} USD = ₹{converted_price:.2f} INR"
    else:  # inr_to_usd
        converted_price = price / exchange_rate
        answer = f"₹{price:.2f} INR = ${converted_price:.2f} USD"

    return render_template('index.html', 
                           user_input="Currency Conversion", 
                           answer=answer)

if __name__ == '__main__':
    app.run(debug=True)