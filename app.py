from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bcrypt import hashpw, gensalt, checkpw
import os
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Context processor for current time
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# AWS Resources
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
user_table = dynamodb.Table('users')
orders_table = dynamodb.Table('orders')

sns = boto3.client('sns', region_name='us-east-1')
SNS_TOPIC_ARN = 'YOUR_SNS_TOPIC_ARN'  # Replace this with your SNS topic ARN

# Email config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = 'kavyasrikoduru18@gmail.com'
EMAIL_PASSWORD = 'ikpo xzcp gbjh atws'

# Product data
veg_pickles = [ 
    {'id': 1, 'name': 'Mango Pickle', 'price': 120, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\mango-pickle.png', 'rating': 5},
    {'id': 2, 'name': 'Lemon Pickle', 'price': 100, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\lemon_pickle.png', 'rating': 4},
    {'id': 3, 'name': 'Tomato Pickle', 'price': 95, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\Tomatopickle.png', 'rating': 5},
    {'id': 4, 'name': 'Amla Pickle', 'price': 85, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\Amla_Pickles.png', 'rating': 4},
    {'id': 5, 'name': 'Tamarind Pickle', 'price': 110, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\tamarind_pickle.png', 'rating': 4},
    {'id': 6, 'name': 'Garlic Pickle', 'price': 95, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\garlic_pickles.png', 'rating': 4},
    {'id': 7, 'name': 'Gongura Pickle', 'price': 105, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\Gongura_pickles.png', 'rating': 5}

]   

non_veg_pickles = [
    {'id': 8, 'name': 'Avakaya Chicken Pickle', 'price': 450, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\Chicken-Aavakaya.png', 'rating': 5},
    {'id': 9, 'name': 'Boneless Chicken Pickle', 'price': 400, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\chicken-boneless-pickle.png', 'rating': 4},
    {'id': 10, 'name': 'Boneless Mutton Pickle', 'price': 400, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\boneless_mutton.png', 'rating': 4},
    {'id': 11, 'name': 'Fish Pickle', 'price': 550, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\fish_pickle.png', 'rating': 4},
    {'id': 12, 'name': 'Gongura Mutton Pickle', 'price': 800, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\GonguraMuttonPickle.png', 'rating': 4},
    {'id': 13, 'name': 'Gongura Prawn Pickle', 'price': 500, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\gongura_prawn.png', 'rating': 4},
    {'id': 14, 'name': 'Spicy Chicken Pickle', 'price': 240, 'weight': '500g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\spicychicken_pickle.png', 'rating': 4}
]

snacks = [
    {'id': 15, 'name': 'Cake Batter', 'price': 80, 'weight': '250g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\cake-batter-dip.png', 'rating': 5},
    {'id': 16, 'name': 'Cheese Crackers', 'price': 100, 'weight': '250g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\cheesy-crackers.png', 'rating': 4},
    {'id': 17, 'name': 'Fries', 'price': 85, 'weight': '250g', 'image': 'C:\Users\sastr\OneDrive\Desktop\Homemade Pickles final\project\static\images\fries.png', 'rating': 4},
    {'id': 18, 'name': 'Grilled Cheese', 'price': 75, 'weight': '250g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\grilled_cheese_cristini.png', 'rating': 4},
    {'id': 19, 'name': 'Peach Crumb', 'price': 65, 'weight': '250g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\Peach-Crumb-Bars.png', 'rating': 4},
    {'id': 20, 'name': 'Potato Chips', 'price': 60, 'weight': '200g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\potato_chips.png', 'rating': 4},
    {'id': 21, 'name': 'Savory Fire Crackers', 'price': 60, 'weight': '200g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\savory_fire_crackers.png', 'rating': 4},
    {'id': 21, 'name': 'Oatmeal Choco Cookies', 'price': 60, 'weight': '200g', 'image': 'C:\Users\sastr\OneDrive\Pictures\Saved Pictures\oatmeal-cookies.png', 'rating': 4}
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/veg_pickles')
def show_veg_pickles():
    return render_template('veg_pickles.html', products=veg_pickles)

@app.route('/non_veg_pickles')
def show_non_veg_pickles():
    return render_template('non_veg_pickles.html', products=non_veg_pickles)

@app.route('/snacks')
def show_snacks():
    return render_template('snacks.html', products=snacks)

@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    results = []
    for item in veg_pickles + non_veg_pickles + snacks:
        if query in item['name'].lower():
            results.append({
                'name': item['name'],
                'image': item['image'],
                'link': '#'
            })
    return render_template('search_results.html', query=query, results=results)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    name = request.form['name']
    message = request.form['message']
    flash(f"Thanks for your review, {name}!")
    return redirect(url_for('home'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    name = request.form['name']
    price = float(request.form['price'])
    weight = request.form['weight']

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    for item in cart:
        if item['name'] == name and item['weight'] == weight:
            item['quantity'] += 1
            break
    else:
        cart.append({'name': name, 'price': price, 'weight': weight, 'quantity': 1})

    session['cart'] = cart
    flash(f"{name} added to cart!", "success")
    return redirect(request.referrer or url_for('home'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart_items=cart, total=total)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    name = request.form['item_name']
    change = int(request.form['change'])
    cart = session.get('cart', [])
    for item in cart:
        if item['name'] == name:
            item['quantity'] += change
            if item['quantity'] <= 0:
                cart.remove(item)
            break
    session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    name = request.form['item_name']
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['name'] != name]
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['fullname']
        email = request.form['email']
        address = request.form['address']
        city = request.form['city']
        pincode = request.form['pincode']
        phone = request.form['phone']
        payment = request.form['payment']
        upi_id = request.form.get('upi_id')
        card_number = request.form.get('card_number')

        cart_items = session.get('cart', [])

        # ✅ Use Decimal for total and each item price
        total = Decimal(str(sum(item['price'] * item['quantity'] for item in cart_items)))
        for item in cart_items:
            item['price'] = Decimal(str(item['price']))

        order_id = str(uuid.uuid4())

        order_data = {
            'order_id': order_id,
            'name': name,
            'address': address,
            'city': city,
            'pincode': pincode,
            'phone': phone,
            'email': email,
            'payment': payment,
            'upi_id': upi_id,
            'card_number': card_number,
            'total': total,
            'items': cart_items
        }

        orders_table.put_item(Item=order_data)

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='New Order',
            Message=f"Order ID: {order_id}\nName: {name}\nTotal: ₹{total}"
        )

        send_email(email, 'Order Confirmation - Homemade Happiness',
                   f'Thank you {name} for your order!\nOrder ID: {order_id}\nTotal: ₹{total}\nPayment: {payment}')

        session.pop('cart', None)
        return render_template('success.html', name=name, order_id=order_id)

    return render_template('checkout.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_id = str(uuid.uuid4())
        user_table.put_item(Item={'User_id': user_id, 'email': email, 'password': password})
        send_email(email, 'Welcome to Homemade Happiness', 'Thank you for signing up!')
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_table.get_item(Key={'email': email}).get('Item')
        if user and user['password'] == password:
            session['user'] = email
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out successfully!", "success")
    return redirect(url_for('index'))

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("Email failed:", e)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
