# init_db.py
import sqlite3, os

DB = "store.db"
if os.path.exists(DB):
    print("Overwriting existing store.db (backup if needed).")

conn = sqlite3.connect(DB)
c = conn.cursor()

# Drop (optional) for fresh start
c.execute("DROP TABLE IF EXISTS products")
c.execute("DROP TABLE IF EXISTS users")

# Products table with category
c.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    image TEXT,
    category TEXT
)
""")

# Users table
c.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
""")

# Insert sample products
products = [
    ("Classic Tee", 499.00, "Soft cotton tee", "tshirt.jpg", "Clothing"),
    ("Slim Jeans", 1299.00, "Comfort denim", "jeans.jpg", "Clothing"),
    ("Running Shoes", 2499.00, "Lightweight running shoes", "shoes.jpg", "Footwear"),
    ("Smart Watch", 5999.00, "Fitness smartwatch", "watch.jpg", "Gadgets"),
    ("Leather Wallet", 799.00, "Genuine leather wallet", "wallet.jpg", "Accessories"),
]
c.executemany("INSERT INTO products (name, price, description, image, category) VALUES (?, ?, ?, ?, ?)", products)

conn.commit()
conn.close()
print("store.db initialized with sample products.")
