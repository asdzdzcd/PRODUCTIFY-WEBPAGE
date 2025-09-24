from flask import Flask, render_template, request, redirect, session, url_for
import pyodbc
import base64
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  


server   = 'localhost'
database = 'WEBSITE'
driver   = '{ODBC Driver 17 for SQL Server}'  

conn = pyodbc.connect(f'DRIVER={driver};'
                      f'SERVER={server};'
                      f'DATABASE={database};'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()


def get_db_connection():
    try:
        return pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        )
    except Exception as e:
        print("Connection failed:", e)
        return None

@app.route('/')
def show_signup():
    return render_template('INDEX.html')

@app.route('/signup', methods=['POST'])
def signup():
    try:
        fullname = request.form['Fullname']
        email = request.form['Email']
        password = request.form['Password']

        conn = get_db_connection()
        if not conn:
            return "Database connection failed."

        cursor = conn.cursor()
        query = "INSERT INTO dbo.signup (fullname, email, password) VALUES (?, ?, ?)"
        cursor.execute(query, (fullname, email, password))
        conn.commit()
        cursor.close()
        conn.close()
        return "<h3> Signup successful!</h3>"
    except Exception as e:
        print("Error:", e)
        return f"<h3> Error occurred: {e}</h3>"
    
@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form['Email']
        password = request.form['Password']

        conn = get_db_connection()
        if not conn:
            return "Database connection failed."

        cursor = conn.cursor()
        query = "INSERT INTO dbo.signup (email, password) VALUES (?, ?)"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return redirect(url_for('landing_page'))
        else:
            return "<h3>Invalid email or password.</h3>"

    except Exception as e:
        print("Login error:", e)
        return f"<h3>Login error occurred: {e}</h3>"

@app.route('/landing')
def landing_page():
    return render_template('LANDING PAGE.HTML')


@app.route('/menswear', methods=['GET', 'POST'])
def menswear():
    if request.method == 'POST':
        file = request.files['image']
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        data = file.read()  

        cursor.execute("""
            INSERT INTO MensWear (name, price, description, image)
            VALUES (?, ?, ?, ?)
        """, name, float(price), description, data)
        conn.commit()
        return redirect('/menswear')

    cursor.execute("SELECT cloth_id, name, price, description, image FROM MensWear")
    rows = cursor.fetchall()
    items = []
    for row in rows:
        img_data = base64.b64encode(row.image).decode('utf-8')  
        items.append({
            'id': row.cloth_id,
            'name': row.name,
            'price': row.price,
            'description': row.description,
            'image_data': img_data
        })
    return render_template('MENSWEAR.html', items=items)


@app.route('/womenswear', methods=['GET', 'POST'])
def womenswear():
    if request.method == 'POST':
        file = request.files['image']
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        data = file.read()  

        cursor.execute("""
            INSERT INTO WomensWear (name, price, description, image)
            VALUES (?, ?, ?, ?)
        """, name, float(price), description, data)
        conn.commit()
        return redirect('/womenswear')

    cursor.execute("SELECT cloth_id, name, price, description, image FROM WomensWear")
    rows = cursor.fetchall()
    items = []
    for row in rows:
        img_data = base64.b64encode(row.image).decode('utf-8')  
        items.append({
            'id': row.cloth_id,
            'name': row.name,
            'price': row.price,
            'description': row.description,
            'image_data': img_data
        })
    return render_template('WOMENSWEAR.html', items=items)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    name    = request.form.get('Name')
    email   = request.form.get('Email')
    rating  = request.form.get('StarRating')
    comment = request.form.get('Comment')
    
    insert_sql = """
        INSERT INTO Reviews (Name, Email, StarRating, Comment)
        VALUES (?, ?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(insert_sql, (name, email, rating, comment))
    conn.commit()   
    return "<h3>Thank you! Your review has been submitted successfully.</h3>"

@app.route('/')
def show_review():
    return render_template('reviewform.html')

@app.route('/reviews')
def show_reviews():
    cursor = conn.cursor()
    cursor.execute("SELECT Name, StarRating, Comment FROM Reviews")
    reviews = cursor.fetchall()
    return render_template('reviewform.html', reviews=reviews)

@app.route('/admin/reviews')
def admin_reviews():
    cursor = conn.cursor()
    cursor.execute("SELECT ReviewID, Name, Email, StarRating, Comment FROM Reviews")
    reviews = cursor.fetchall()
    return render_template('reviewform.html', reviews=reviews)

@app.route('/reviewform')
def review_form():
    return render_template('reviewform.html')


@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if request.method == 'GET':
        
        category = request.args.get('category')
        cloth_id = request.args.get('id', type=int)
        if category not in ('mens','womens') or not cloth_id:
            return "Invalid product", 400

        
        table = 'MensWear' if category=='mens' else 'WomensWear'
        cursor.execute(f"SELECT name, price, description, image FROM {table} WHERE cloth_id = ?", cloth_id)
        row = cursor.fetchone()
        if not row:
            return "Product not found", 404

        
        img_data = base64.b64encode(row.image).decode('utf-8')
        return render_template('checkout.html',
                               category=category,
                               id=cloth_id,
                               name=row.name,
                               price=row.price,
                               description=row.description,
                               image_data=img_data)

    
    category      = request.form['category']
    cloth_id      = int(request.form['id'])
    buyer_name    = request.form['buyer_name']
    buyer_mobile  = request.form['buyer_mobile']
    buyer_address = request.form['buyer_address']

    
    table = 'MensWear' if category=='mens' else 'WomensWear'
    cursor.execute(f"SELECT name, price, description FROM {table} WHERE cloth_id = ?", cloth_id)
    row = cursor.fetchone()
    if not row:
        return "Product not found", 404

    
    insert_sql = """
      INSERT INTO Orders
        (ProductName, ProductPrice, ProductDescription, BuyerName, BuyerMobile, BuyerAddress)
        OUTPUT INSERTED.OrderID
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_sql, (
      row.name, float(row.price), row.description,
      buyer_name, buyer_mobile, buyer_address
    ))
    order_id_row = cursor.fetchone()
    conn.commit()

    if not order_id_row:
        return "Error creating order", 500

    order_id = order_id_row[0]
    return redirect(url_for('payment', order_id=order_id))


@app.route('/payment')
def payment():
    order_id = request.args.get('order_id', type=int)
    if not order_id:
        return "Missing order ID", 400
    
    return render_template('payment.html', order_id=order_id)

#  ➜ Handle card submission
@app.route('/process_payment', methods=['POST'])
def process_payment():
    order_id      = int(request.form['order_id'])
    card_number   = request.form['card_number']
    expiry_month  = int(request.form['expiry_month'])
    expiry_year   = int(request.form['expiry_year'])
    cvv           = request.form['cvv']

    # Insert into CardDetails
    insert_sql = """
      INSERT INTO CardDetails 
        (OrderID, CardNumber, ExpiryMonth, ExpiryYear, CVV)
      VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(insert_sql,
        order_id, card_number, expiry_month, expiry_year, cvv
    )
    conn.commit()

    return """
      <h3>✅ Payment successful!</h3>
      <p>Your order #{} is confirmed and ready for shipment.</p>
    """.format(order_id)

# ─── Admin: View all orders ───────────────────────────────────
@app.route('/admin/orders')
def admin_orders():
    cursor.execute("""
        SELECT OrderID, ProductName, BuyerName, BuyerMobile, BuyerAddress, Status
        FROM Orders
        ORDER BY OrderID DESC
    """)
    orders = cursor.fetchall()
    return render_template('admin_orders.html', orders=orders)

# ─── Admin: Update an order’s status ──────────────────────────
@app.route('/admin/update_status', methods=['POST'])
def update_status():
    order_id   = int(request.form['order_id'])
    new_status = request.form['new_status']
    cursor.execute(
        "UPDATE Orders SET Status = ? WHERE OrderID = ?",
        new_status, order_id
    )
    conn.commit()
    return redirect(url_for('admin_orders'))


# ----------------------------------------
# ✅ RUN APP
# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
