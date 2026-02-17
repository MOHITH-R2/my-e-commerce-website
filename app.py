import os

from flask import Flask, abort, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import or_

from models import db, Product, User

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# -----------------------------
# Initialize cart in session
# -----------------------------
@app.before_request
def before_request():
    if 'cart' not in session:
        session['cart'] = {}

@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})
    count = sum(cart.values())
    return {"cart_count": count}

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
def seed_products():
    if Product.query.first():
        return

    sample_products = [
        Product(name="T-Shirt", price=499, category="Clothing", image="tshirts.jpg", description="Comfortable cotton t-shirt"),
        Product(name="Shoes", price=2999, category="Footwear", image="shoes.jpg", description="Stylish running shoes"),
        Product(name="Phone", price=15000, category="Electronics", image="phone.png", description="Latest smartphone"),
        Product(name="Headphones", price=2500, category="Electronics", image="headphones.png", description="Wireless headphones"),
        Product(name="Laptop", price=55000, category="Electronics", image="laptop.png", description="High performance laptop"),
    ]
    db.session.add_all(sample_products)
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_products()

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    products = Product.query.order_by(Product.id.asc()).all()
    categories = sorted({p.category for p in products if p.category})
    return render_template('index.html', products=products, categories=categories)

@app.route('/product/<int:id>')
def product(id):
    product = Product.query.get(id)
    if not product:
        abort(404)
    related = Product.query.filter(Product.id != id).limit(4).all()
    return render_template('product.html', product=product, related_products=related)

# -----------------------------
# Cart routes
# -----------------------------
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if not Product.query.get(id):
        abort(404)
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
    products = Product.query.filter(Product.id.in_([int(i) for i in cart.keys()])).all() if cart else []
    for p in products:
        qty = cart.get(str(p.id), 0)
        if qty > 0:
            items.append({'product': p, 'qty': qty, 'subtotal': p.price * qty})
            total += p.price * qty
    return render_template('cart.html', items=items, total=total)

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    if request.method == 'POST':
        session['cart'] = {}
        return render_template('checkout.html', success=True)
    return render_template('checkout.html', success=False)

# -----------------------------
# User system (database-backed)
# -----------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        confirm_password = request.form.get('confirm_password','')
        if not username or not password:
            flash('Fill all fields', 'error')
            return redirect(url_for('register'))
        if not email:
            flash('Email is required', 'error')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter(or_(User.username == username, User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))

        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Account created. Login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        next_url = request.args.get("next", "")
        user = User.query.filter(or_(User.username == username, User.email == username.lower())).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f'Welcome back {user.username}!', 'success')
        if next_url.startswith("/"):
            return redirect(next_url)
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
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
