from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret"

# -----------------------------
# Initialize cart in session
# -----------------------------
@app.before_request
def before_request():
    if 'cart' not in session:
        session['cart'] = {}

# -----------------------------
# Login required decorator
# -----------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# -----------------------------
# Product Data (sample)
# -----------------------------
PRODUCTS = [
    {'id':1,'name':'T-Shirt','price':499,'category':'Clothing','image':'tshirts.jpg','description':'Comfortable cotton t-shirt'},
    {'id':2,'name':'Shoes','price':2999,'category':'Footwear','image':'shoes.jpg','description':'Stylish running shoes'},
    {'id':3,'name':'Phone','price':15000,'category':'Electronics','image':'phone.png','description':'Latest smartphone'},
    {'id':4,'name':'Headphones','price':2500,'category':'Electronics','image':'headphones.png','description':'Wireless headphones'},
    {'id':5,'name':'Laptop','price':55000,'category':'Electronics','image':'laptop.png','description':'High performance laptop'},
]

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    categories = list(set([p['category'] for p in PRODUCTS]))
    return render_template('index.html', products=PRODUCTS, categories=categories)

@app.route('/product/<int:id>')
def product(id):
    product = next((p for p in PRODUCTS if p['id']==id), None)
    if not product:
        return "Product not found", 404
    related = [p for p in PRODUCTS if p['id'] != id]
    return render_template('product.html', product=product, related_products=related)

# -----------------------------
# Cart routes
# -----------------------------
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    cart = session.get('cart', {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session['cart'] = cart
    flash('Added to cart!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for p in PRODUCTS:
        qty = cart.get(str(p['id']), 0)
        if qty > 0:
            items.append({'product': p, 'qty': qty, 'subtotal': p['price']*qty})
            total += p['price']*qty
    return render_template('cart.html', items=items, total=total)

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    if request.method == 'POST':
        session['cart'] = {}
        return render_template('checkout.html', success=True)
    return render_template('checkout.html', success=False)

# -----------------------------
# Simple User system (session-based)
# -----------------------------
USERS = {}  # username: {password_hash, username}

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if not username or not password:
            flash('Fill all fields', 'error')
            return redirect(url_for('register'))
        if username in USERS:
            flash('Username exists', 'error')
            return redirect(url_for('register'))
        USERS[username] = {'username': username, 'password_hash': generate_password_hash(password)}
        flash('Account created. Login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = USERS.get(username)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))
        session['user_id'] = username
        session['username'] = username
        flash(f'Welcome back {username}!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# -----------------------------
# Run app
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
