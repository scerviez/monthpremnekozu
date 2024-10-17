from flask import Flask, request, jsonify, render_template
import random
import string
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# MongoDB setup
mongo_url = 'mongodb+srv://nekozuX:farih2009@nekozu.wlvpzbo.mongodb.net/?retryWrites=true&w=majority&appName=nekozu'
client = MongoClient(mongo_url)
db = client['redeem_db']
one_week_prem = db['1week_prem']
one_month_prem = db['1month_prem']
redeemdb = db['redeem_db']
transactionsCollection = db['transactions']

# Generate random Redeem code
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route('/')
def index():
    return render_template('main.html')

# Generate code after validating the Ko-fi payment URL
@app.route('/generate', methods=['POST'])
def generate_code_route():
    payment_url = request.json.get('payment_url')  # Get the user's payment URL from the JSON body

    # Check if the payment URL exists in the 1-month collection
    transaction = transactionsCollection.find_one({'url': payment_url})
    premium_type = '1-month'

    if not transaction:
        return jsonify({'error': True, 'message': 'Invalid payment URL or payment not found.'}), 400

    # Generate redeem code
    code = generate_code(8)
    expiry = datetime.now() + timedelta(weeks=4)  # Set expiry to 4 weeks (1 month)

    # Store the redeem code in the 1-month collection
    db['codes'].insert_one({
        'code': code,
        'expiry': expiry,
        'used': False,
        'premium_type': premium_type
    })

    # Remove the used payment URL entry from the collection
    transactionsCollection.delete_one({'url': payment_url})

    return jsonify({'redeem_code': code, 'expiry': expiry, 'premium_type': premium_type})

# Redeem the generated code
@app.route('/redeem', methods=['POST'])
def redeem_code():
    code = request.form['code']

    # Check if the code exists and hasn't been used yet
    redeem_code = db['codes'].find_one({'code': code})

    if not redeem_code:
        return "Invalid or expired code", 400

    if redeem_code['used']:
        return "Code already used", 400

    # Mark the code as used
    db['codes'].update_one({'_id': redeem_code['_id']}, {'$set': {'used': True}})
    return "Code redeemed successfully!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)

