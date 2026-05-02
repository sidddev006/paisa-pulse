import sqlite3
from dotenv import load_dotenv
load_dotenv()
import csv
import io  
import os
import psycopg2
from flask import g
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, redirect, session, url_for, g, make_response, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
import urllib.parse

app = Flask(__name__)
app.secret_key = "something"

DATABASE = "finance.db"

raw_url = os.environ.get("DATABASE_URL")
if raw_url and "://password@" not in raw_url:
    pass

DATABASE_URL = raw_url

#---DB helpers---
def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return g.db

@app.teardown_appcontext
def close_db(e = None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    # Connect directly to run setup
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # PostgreSQL uses SERIAL for auto-incrementing IDs[cite: 1]
    # Dates are handled more strictly as DATE types[cite: 1]
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id), 
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            date DATE NOT NULL
        )
    """)
    
    conn.commit() # Important: Changes aren't saved until committed[cite: 1]
    cur.close()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

#-- Routes----
@app.route("/")
def index():
    # Landing page
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            flash("invalid username")
            return render_template("register.html")
            
        db = get_db()
        cur = db.cursor() # Create cursor
        
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        users = cur.fetchone()
        
        if users:
            cur.close()
            flash("username already exists")
            return render_template("register.html")
            
        password = request.form.get("password")
        pass_confirm = request.form.get("pass_confirm")
        if password != pass_confirm:
            cur.close()
            flash("Both the passwords should be the same")
            return render_template("register.html")
            
        pass_hash = generate_password_hash(password)
        
        # INSERT requires commit on the connection object
        cur.execute("INSERT INTO users(username, hash) VALUES(%s,%s)", (username, pass_hash))
        db.commit() 
        
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        rows = cur.fetchone()
        
        session["user_id"] = rows["id"]
        session["username"] = username
        
        cur.close() # Close cursor
        return redirect("/dashboard")
        
    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        db = get_db()
        cur = db.cursor()
        
        cur.execute("SELECT * FROM users WHERE username = %s", (username, ))
        check_username = cur.fetchone()
        
        if not check_username:
            cur.close()
            flash("Username does not exists")
            return render_template("login.html")
            
        if not check_password_hash(check_username["hash"], password):
            cur.close()
            flash("incorrect password")
            return render_template("login.html")
            
        session["username"] = username
        session["user_id"] = check_username["id"]
        
        cur.close()
        return redirect("/dashboard")
        
    return render_template("login.html")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        type = request.form.get("type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        date = request.form.get("date")
        note = request.form.get("note")
        
        if not amount or not category or not type:
            flash("Please fill all the required fields")
            return render_template("add.html")
            
        db = get_db()
        cur = db.cursor()
        
        user_id = session["user_id"]
        
        # Ensure %s is used and connection is committed
        cur.execute("INSERT INTO transactions(type, category, amount, date, note, user_id) VALUES(%s,%s,%s,%s,%s,%s)", 
                    (type, category, amount, date, note, user_id))
        db.commit()
        
        cur.close()
        flash("Transaction added successfully!")
        return redirect("/dashboard")
        
    return render_template("add.html")

@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    user_id = session["user_id"]
    db = get_db()
    cur = db.cursor() # Create a cursor for PostgreSQL

    # Change 1: Use %s placeholders
    cur.execute("SELECT SUM(amount) as amount FROM transactions WHERE user_id = %s AND type = %s", (user_id, "income"))
    total_income_row = cur.fetchone()
    # Access by key because we used DictCursor in get_db()
    total_income = total_income_row["amount"] if total_income_row and total_income_row["amount"] else 0
    
    cur.execute("SELECT SUM(amount) as amount FROM transactions WHERE user_id = %s AND type = %s", (user_id, "expense"))
    total_expenses_row = cur.fetchone()
    total_expenses = total_expenses_row["amount"] if total_expenses_row and total_expenses_row["amount"] else 0
    
    balance = total_income - total_expenses
    
    cur.execute("SELECT category, SUM(amount) as amount FROM transactions WHERE user_id = %s AND type = %s GROUP BY category", (user_id, "expense"))
    expense_by_category = cur.fetchall()
    
    cur.execute("SELECT * FROM transactions WHERE user_id = %s ORDER BY date DESC LIMIT 5", (user_id, ))
    recent_transactions = cur.fetchall()

    # Change 2: Use TO_CHAR and CURRENT_DATE for PostgreSQL date math
    # PostgreSQL doesn't have strftime or date('now', '-6 months')
    cur.execute("""
        SELECT TO_CHAR(date, 'YYYY-MM') as month, SUM(amount) as total, type 
        FROM transactions 
        WHERE date >= CURRENT_DATE - INTERVAL '6 months' AND user_id = %s 
        GROUP BY month, type
    """, (user_id, ))
    monthly_data = cur.fetchall()
    
    expense_labels = [row["category"] for row in expense_by_category]
    expense_amounts = [row["amount"] for row in expense_by_category]
    
    income_monthly = {}
    expense_monthly = {}
    for row in monthly_data:
        if row["type"] == "income":
            income_monthly[row["month"]] = row["total"]
        else:
            expense_monthly[row["month"]] = row["total"]
            
    months = []
    for i in range(5, -1, -1):
        d = datetime.now().replace(day=1) - timedelta(days=i * 30)
        months.append(d.strftime("%Y-%m"))
        
    current_month = datetime.now().strftime("%Y-%m")
    this_month_income = income_monthly.get(current_month, 0)
    this_month_expense = expense_monthly.get(current_month, 0)
    
    last_month = (datetime.now().replace(day=1) - timedelta(days=1 * 30)).strftime("%Y-%m")
    last_month_expense = expense_monthly.get(last_month, 0)
    
    saved = this_month_income - this_month_expense
    overspending = this_month_expense - last_month_expense
    
    if not expense_by_category:
        biggest_category = "None"
        biggest_amount = 0
    else:
        biggest = max(expense_by_category, key=lambda row: row["amount"])
        biggest_category = biggest["category"]
        biggest_amount = biggest["amount"]
        
    percentage = round((biggest_amount / this_month_expense) * 100) if this_month_expense else 0
    
    cur.close() # Always close the cursor when done[cite: 1]
    
    return render_template("dashboard.html", 
                           percentage=percentage, 
                           saved=saved, 
                           overspending=overspending, 
                           this_month_expense=this_month_expense,
                           biggest_category=biggest_category, 
                           biggest_amount=biggest_amount, 
                           total_income=total_income, 
                           total_expense=total_expenses, 
                           balance=balance, 
                           expense_by_category=expense_by_category, 
                           recent_transactions=recent_transactions, 
                           monthly_data=monthly_data, 
                           expense_labels=expense_labels, 
                           expense_amounts=expense_amounts, 
                           income_monthly=income_monthly, 
                           expense_monthly=expense_monthly, 
                           months=months)

@app.route("/history", methods=["POST", "GET"])
@login_required
def history():
    user_id = session["user_id"]
    db = get_db()
    cur = db.cursor() # Use cursor for PostgreSQL
    
    filter_type = request.args.get("type", "")
    filter_category = request.args.get("category", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # Base query
    query = "SELECT * FROM transactions WHERE user_id = %s"
    params = [user_id]
    
    # Conditional filtering
    if filter_type:
        query += " AND type = %s"
        params.append(filter_type)

    if filter_category:
        query += " AND category = %s"
        params.append(filter_category)
    
    if date_from and date_to:
        query += " AND date >= %s AND date <= %s"
        params.append(date_from)
        params.append(date_to)
    elif date_from:
        query += " AND date >= %s"
        params.append(date_from)
    elif date_to:
        query += " AND date <= %s"
        params.append(date_to)
    
    # Execute through cursor
    cur.execute(query, params)
    results = cur.fetchall()
    
    # Summary calculations (using DictCursor keys)
    summary_income = sum(row["amount"] for row in results if row["type"] == "income")
    summary_expense = sum(row["amount"] for row in results if row["type"] == "expense")
    total_count = len(results)
    net = summary_income - summary_expense
    
    cur.close()
    return render_template("history.html", results=results, summary_income=summary_income, 
                           summary_expense=summary_expense, total_count=total_count, net=net)

@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    user_id = session["user_id"]
    db = get_db()
    cur = db.cursor()
    
    # Placeholders must be %s
    cur.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (id, user_id))
    db.commit() # Changes must be committed
    
    cur.close()
    return redirect("/history")

@app.route("/export")
@login_required
def export():
    user_id = session["user_id"]
    db = get_db()
    cur = db.cursor()
    
    cur.execute("SELECT * FROM transactions WHERE user_id = %s", (user_id,))
    transactions = cur.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Date", "Type", "Category", "Note", "Amount"])
    
    for row in transactions:
        # Accessing by column names works because of DictCursor[cite: 1]
        writer.writerow([row["date"], row["type"], row["category"], row["note"], row["amount"]])
    
    cur.close()
    output.seek(0)
    return Response(output, mimetype="text/csv", 
                    headers={"Content-Disposition": "attachment;filename=transactions.csv"})

@app.route("/logout") # No trailing slash if your links don't use one
@login_required
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)