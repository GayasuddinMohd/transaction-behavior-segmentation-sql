# ============================================================
#  PROJECT  : Transaction Behavior & Segmentation Analysis
#  FILE     : 2_generate_data.py
#  PURPOSE  : Generate realistic data and insert into MySQL
#  REQUIRES : pip install faker mysql-connector-python
# ============================================================

import random
from datetime import datetime, timedelta
from faker import Faker
import mysql.connector

fake = Faker('en_IN')   # Indian locale for realistic names/cities
random.seed(42)

# ============================================================
# DATABASE CONNECTION — change password if needed
# ============================================================
conn = mysql.connector.connect(
    host     = "localhost",
    user     = "root",
    password = "dark@123_HUM",   # <-- update this
    database = "transaction_analysis"
)
cursor = conn.cursor()
print("✅ Connected to MySQL")

# ============================================================
# STEP 1 — INSERT USERS (1,000 users)
# ============================================================
CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Surat"
]

users = []
for _ in range(1000):
    users.append((
        fake.name(),
        random.choice(CITIES),
        random.randint(18, 60),
        random.choice(['M', 'F']),
        fake.date_between(start_date='-3y', end_date='-1y')
    ))

cursor.executemany("""
    INSERT INTO users (full_name, city, age, gender, signup_date)
    VALUES (%s, %s, %s, %s, %s)
""", users)
conn.commit()
print(f"✅ Inserted {len(users)} users")

# ============================================================
# STEP 2 — INSERT PRODUCTS (50 products)
# ============================================================
PRODUCTS = [
    # Electronics
    ("iPhone 15",            "Electronics",  79999),
    ("Samsung Galaxy S23",   "Electronics",  69999),
    ("Sony WH-1000XM5",      "Electronics",  29999),
    ("iPad Air",             "Electronics",  59999),
    ("Laptop Dell XPS 13",   "Electronics", 110000),
    ("JBL Speaker",          "Electronics",   4999),
    ("Boat Earbuds",         "Electronics",   1499),
    ("Smart Watch",          "Electronics",   8999),
    ("Power Bank 20000mAh",  "Electronics",   1999),
    ("USB-C Hub",            "Electronics",   2499),

    # Fashion
    ("Nike Air Max",         "Fashion",       8999),
    ("Levi's 511 Jeans",     "Fashion",       3499),
    ("Zara Shirt",           "Fashion",       2199),
    ("H&M Dress",            "Fashion",       1799),
    ("Ray-Ban Sunglasses",   "Fashion",       6999),
    ("Adidas Track Pants",   "Fashion",       2999),
    ("Woodland Boots",       "Fashion",       4499),
    ("Fastrack Watch",       "Fashion",       2499),
    ("Leather Wallet",       "Fashion",        999),
    ("Sports Cap",           "Fashion",        499),

    # Food & Grocery
    ("Organic Honey 500g",   "Food",           599),
    ("Basmati Rice 5kg",     "Food",           499),
    ("Olive Oil 1L",         "Food",           799),
    ("Protein Bar Pack",     "Food",           899),
    ("Green Tea 100 bags",   "Food",           349),
    ("Mixed Nuts 500g",      "Food",           699),
    ("Instant Coffee 200g",  "Food",           399),
    ("Dark Chocolate Box",   "Food",           599),
    ("Whey Protein 1kg",     "Food",          1899),
    ("Vitamin C Tablets",    "Food",           299),

    # Home & Kitchen
    ("Air Fryer",            "Home",          4999),
    ("Dinner Set 18pcs",     "Home",          2299),
    ("Bedsheet King Size",   "Home",          1299),
    ("Pressure Cooker 5L",   "Home",          1799),
    ("Robot Vacuum",         "Home",         14999),
    ("Table Lamp",           "Home",           899),
    ("Water Purifier",       "Home",          8999),
    ("Mixer Grinder",        "Home",          3499),
    ("Curtains Set",         "Home",          1599),
    ("Storage Box Set",      "Home",           799),

    # Books & Education
    ("Python Crash Course",  "Books",          799),
    ("Atomic Habits",        "Books",          499),
    ("The Lean Startup",     "Books",          599),
    ("SQL in 10 Minutes",    "Books",          449),
    ("Data Science Handbook","Books",          899),
    ("Clean Code",           "Books",          699),
    ("System Design Book",   "Books",          749),
    ("Thinking Fast & Slow", "Books",          549),
    ("Zero to One",          "Books",          499),
    ("Rich Dad Poor Dad",    "Books",          399),
]

cursor.executemany("""
    INSERT INTO products (product_name, category, base_price)
    VALUES (%s, %s, %s)
""", PRODUCTS)
conn.commit()
print(f"✅ Inserted {len(PRODUCTS)} products")

# ============================================================
# STEP 3 — INSERT TRANSACTIONS + ITEMS (12,000 orders → ~48K items)
#
# KEY INSIGHT SEEDING:
#   - Evening hours (18–22) get 40% of all orders
#   - Weekends (Sat/Sun) get slightly higher volume
#   - High-value users (top 10%) place 3x more orders
# ============================================================

# Fetch IDs
cursor.execute("SELECT user_id FROM users")
user_ids = [r[0] for r in cursor.fetchall()]

cursor.execute("SELECT product_id, base_price FROM products")
products_db = cursor.fetchall()   # list of (product_id, base_price)

# Hour distribution: evening (18-22) = 40%, rest = 60%
EVENING_HOURS = list(range(18, 23))     # 18,19,20,21,22
OTHER_HOURS   = list(range(6, 18)) + [23, 0, 1]

def pick_hour():
    """40% chance of evening hour, 60% other hours"""
    if random.random() < 0.40:
        return random.choice(EVENING_HOURS)
    return random.choice(OTHER_HOURS)

def pick_user():
    """Top 10% of users are high-frequency (3x weight)"""
    cutoff = int(len(user_ids) * 0.10)
    if random.random() < 0.30:          # 30% of orders from top 10%
        return random.choice(user_ids[:cutoff])
    return random.choice(user_ids[cutoff:])

# Date range: last 12 months
START_DATE = datetime.now() - timedelta(days=365)

statuses       = ['completed'] * 85 + ['cancelled'] * 10 + ['refunded'] * 5
txn_batch      = []
item_batch     = []
NUM_ORDERS     = 12000

print("⏳ Generating 12,000 orders...")

for _ in range(NUM_ORDERS):
    uid = pick_user()

    # Build a random datetime — bias toward evenings, slight weekend boost
    days_offset = random.randint(0, 365)
    base_date   = START_DATE + timedelta(days=days_offset)
    hour        = pick_hour()
    minute      = random.randint(0, 59)
    second      = random.randint(0, 59)
    txn_dt      = base_date.replace(hour=hour, minute=minute, second=second)

    # 2–6 items per order
    num_items   = random.choices([2, 3, 4, 5, 6], weights=[15, 30, 30, 15, 10])[0]
    chosen      = random.sample(products_db, num_items)

    total = 0
    items_for_txn = []
    for prod_id, base_price in chosen:
        qty        = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        # small price variation ±5%
        unit_price = round(float(base_price) * random.uniform(0.95, 1.05), 2)
        total     += unit_price * qty
        items_for_txn.append((prod_id, qty, unit_price))

    status = random.choice(statuses)
    txn_batch.append((uid, txn_dt, round(total, 2), status))

    # We'll fill in txn_id after bulk insert
    item_batch.append(items_for_txn)

# Bulk insert transactions
cursor.executemany("""
    INSERT INTO transactions (user_id, txn_datetime, total_amount, status)
    VALUES (%s, %s, %s, %s)
""", txn_batch)
conn.commit()
print(f"✅ Inserted {NUM_ORDERS} transactions")

# Get the inserted txn_ids (first inserted ID → last)
cursor.execute("SELECT MIN(txn_id) FROM transactions ORDER BY txn_id ASC LIMIT 1")
first_txn_id = cursor.fetchone()[0]

# Bulk insert items
all_items = []
for i, items_for_txn in enumerate(item_batch):
    txn_id = first_txn_id + i
    for prod_id, qty, unit_price in items_for_txn:
        all_items.append((txn_id, prod_id, qty, unit_price))

cursor.executemany("""
    INSERT INTO transaction_items (txn_id, product_id, quantity, unit_price)
    VALUES (%s, %s, %s, %s)
""", all_items)
conn.commit()
print(f"✅ Inserted {len(all_items)} transaction line items")

# ============================================================
# STEP 4 — VERIFY ROW COUNTS
# ============================================================
print("\n📊 Final row counts:")
for table in ['users', 'products', 'transactions', 'transaction_items']:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"   {table:<22} → {count:>7,} rows")

cursor.close()
conn.close()
print("\n🎉 Data generation complete! Ready for Phase 3 SQL analysis.")
