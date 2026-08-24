import os
import csv
import io
from datetime import datetime, date, timedelta
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import (
    Flask, render_template, request, redirect, session, 
    url_for, g, flash, Response, jsonify, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db, close_db, query_db, init_db, detect_db_type

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "paisa-pulse-default-secret-key-change-in-production")

# Register teardown to close db connections
app.teardown_appcontext(close_db)

# Auto-initialize database on application load (works for both direct python and gunicorn WSGI)
with app.app_context():
    init_db()

# --- Category Meta Definitions ---
CATEGORY_ICONS = {
    # Expenses
    "food": {"icon": "bi-cup-hot-fill", "color": "amber", "label": "Food & Dining", "emoji": "🍔"},
    "rent": {"icon": "bi-house-door-fill", "color": "indigo", "label": "Rent & Housing", "emoji": "🏠"},
    "transport": {"icon": "bi-car-front-fill", "color": "blue", "label": "Transport", "emoji": "🚗"},
    "entertainment": {"icon": "bi-film", "color": "purple", "label": "Entertainment", "emoji": "🎬"},
    "shopping": {"icon": "bi-bag-heart-fill", "color": "pink", "label": "Shopping", "emoji": "🛍️"},
    "health": {"icon": "bi-heart-pulse-fill", "color": "rose", "label": "Health & Medical", "emoji": "💊"},
    "education": {"icon": "bi-book-half", "color": "cyan", "label": "Education", "emoji": "📚"},
    "utilities": {"icon": "bi-lightning-charge-fill", "color": "yellow", "label": "Bills & Utilities", "emoji": "⚡"},
    "other": {"icon": "bi-three-dots", "color": "slate", "label": "Other Expense", "emoji": "📦"},
    # Income
    "salary": {"icon": "bi-briefcase-fill", "color": "emerald", "label": "Salary", "emoji": "💼"},
    "freelance": {"icon": "bi-laptop", "color": "teal", "label": "Freelance", "emoji": "💻"},
    "investment": {"icon": "bi-graph-up-arrow", "color": "green", "label": "Investments", "emoji": "📈"},
    "gift": {"icon": "bi-gift-fill", "color": "violet", "label": "Gifts", "emoji": "🎁"},
    "business": {"icon": "bi-shop", "color": "sky", "label": "Business", "emoji": "🏢"},
    "other_income": {"icon": "bi-cash-coin", "color": "emerald", "label": "Other Income", "emoji": "💰"}
}

def get_category_info(cat_name):
    """Normalize and get category metadata."""
    if not cat_name:
        return {"icon": "bi-tag-fill", "color": "slate", "label": "General", "emoji": "🏷️"}
    normalized = cat_name.strip().lower()
    return CATEGORY_ICONS.get(normalized, {
        "icon": "bi-tag-fill", 
        "color": "blue", 
        "label": cat_name.capitalize(), 
        "emoji": "🏷️"
    })

# --- Jinja Context Processors & Filters ---
@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now().year,
        "db_type": getattr(g, "db_type", detect_db_type()),
        "get_category_info": get_category_info
    }

@app.template_filter("currency")
def format_currency(value):
    """Format numeric values with Indian comma notation and 2 decimals."""
    if value is None:
        return "0.00"
    try:
        val = float(value)
        # Format with standard comma grouping
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

@app.template_filter("date_fmt")
def format_date_filter(value):
    """Format dates to human readable string."""
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%d %b %Y")
    try:
        dt = datetime.strptime(str(value)[:10], "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(value)

# --- Authentication Helper ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        
        # Verify the user exists in the active database (prevents foreign key / stale session issues)
        user = query_db("SELECT id, username FROM users WHERE id = %s", (user_id,), one=True)
        if not user:
            session.clear()
            flash("Your session has expired or the database was refreshed. Please log in again.", "warning")
            return redirect(url_for("login"))
            
        return f(*args, **kwargs)
    return decorated

# --- Routes ---

@app.route("/favicon.ico")
def favicon():
    """Serve favicon icon directly."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )

@app.route("/")
def index():
    """Landing Page"""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/health")
def health():
    """Health check endpoint for Render / monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": detect_db_type()
    })

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user account."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        pass_confirm = request.form.get("pass_confirm", "")

        if not username:
            flash("Username is required.", "danger")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "danger")
            return render_template("register.html", username=username)

        if not password:
            flash("Password is required.", "danger")
            return render_template("register.html", username=username)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", username=username)

        if password != pass_confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", username=username)

        existing_user = query_db("SELECT id FROM users WHERE username = %s", (username,), one=True)
        if existing_user:
            flash("That username is already taken. Please choose another.", "warning")
            return render_template("register.html")

        pass_hash = generate_password_hash(password)
        query_db("INSERT INTO users(username, hash) VALUES(%s, %s)", (username, pass_hash), commit=True)

        user = query_db("SELECT id, username FROM users WHERE username = %s", (username,), one=True)
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash(f"Welcome aboard, {username}! Your account has been created.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """User Sign In."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html", username=username)

        user = query_db("SELECT * FROM users WHERE username = %s", (username,), one=True)

        if not user or not check_password_hash(user["hash"], password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html", username=username)

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        next_page = request.args.get("next")
        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(next_page if next_page else url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    """User Log Out."""
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    """Main Financial Dashboard."""
    user_id = session["user_id"]

    # 1. Total Income & Expense Totals (All-time)
    income_row = query_db(
        "SELECT SUM(amount) as total FROM transactions WHERE user_id = %s AND type = 'income'", 
        (user_id,), one=True
    )
    expense_row = query_db(
        "SELECT SUM(amount) as total FROM transactions WHERE user_id = %s AND type = 'expense'", 
        (user_id,), one=True
    )

    total_income = float(income_row["total"] or 0) if income_row else 0.0
    total_expense = float(expense_row["total"] or 0) if expense_row else 0.0
    balance = total_income - total_expense

    # 2. Category Breakdown for Expenses (All-time or recent)
    category_rows = query_db(
        "SELECT category, SUM(amount) as total FROM transactions WHERE user_id = %s AND type = 'expense' GROUP BY category ORDER BY total DESC",
        (user_id,)
    )
    expense_by_category = [
        {"category": row["category"], "amount": float(row["total"] or 0)} 
        for row in category_rows
    ]

    expense_labels = [row["category"].capitalize() for row in expense_by_category]
    expense_amounts = [row["amount"] for row in expense_by_category]

    # 3. Monthly Trends (Past 6 Months)
    # Calculate past 6 months dates in Python for universal DB compatibility
    today = date.today()
    six_months_ago = (today.replace(day=1) - timedelta(days=150)).replace(day=1)

    all_recent = query_db(
        "SELECT type, amount, date FROM transactions WHERE user_id = %s AND date >= %s ORDER BY date ASC",
        (user_id, six_months_ago.strftime("%Y-%m-%d"))
    )

    income_monthly = {}
    expense_monthly = {}

    for row in all_recent:
        d_str = str(row["date"])[:7] # Format: YYYY-MM
        amt = float(row["amount"] or 0)
        if row["type"] == "income":
            income_monthly[d_str] = income_monthly.get(d_str, 0.0) + amt
        else:
            expense_monthly[d_str] = expense_monthly.get(d_str, 0.0) + amt

    # Generate sequence of last 6 month labels
    months = []
    month_display_labels = []
    for i in range(5, -1, -1):
        # Approximate month subtraction safely
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_key = f"{year:04d}-{month:02d}"
        months.append(m_key)
        m_date = date(year, month, 1)
        month_display_labels.append(m_date.strftime("%b %Y"))

    current_month_key = today.strftime("%Y-%m")
    this_month_income = income_monthly.get(current_month_key, 0.0)
    this_month_expense = expense_monthly.get(current_month_key, 0.0)

    # Previous Month Key
    prev_year = today.year
    prev_month = today.month - 1
    if prev_month <= 0:
        prev_month = 12
        prev_year -= 1
    prev_month_key = f"{prev_year:04d}-{prev_month:02d}"
    last_month_expense = expense_monthly.get(prev_month_key, 0.0)

    saved_this_month = this_month_income - this_month_expense
    overspending = this_month_expense - last_month_expense if last_month_expense > 0 else 0.0
    savings_rate = round((saved_this_month / this_month_income * 100)) if this_month_income > 0 and saved_this_month > 0 else 0

    # 4. Biggest Expense Category
    if expense_by_category:
        biggest_category = expense_by_category[0]["category"].capitalize()
        biggest_amount = expense_by_category[0]["amount"]
        biggest_percentage = round((biggest_amount / total_expense * 100)) if total_expense > 0 else 0
    else:
        biggest_category = "None"
        biggest_amount = 0.0
        biggest_percentage = 0

    # 5. Recent 5 Transactions
    recent_transactions = query_db(
        "SELECT * FROM transactions WHERE user_id = %s ORDER BY date DESC, id DESC LIMIT 5",
        (user_id,)
    )

    # 6. Total Transactions Count
    count_row = query_db("SELECT COUNT(*) as total FROM transactions WHERE user_id = %s", (user_id,), one=True)
    total_transactions_count = count_row["total"] if count_row else 0

    return render_template(
        "dashboard.html",
        balance=balance,
        total_income=total_income,
        total_expense=total_expense,
        this_month_income=this_month_income,
        this_month_expense=this_month_expense,
        saved=saved_this_month,
        overspending=overspending,
        savings_rate=savings_rate,
        biggest_category=biggest_category,
        biggest_amount=biggest_amount,
        percentage=biggest_percentage,
        expense_by_category=expense_by_category,
        recent_transactions=recent_transactions,
        total_transactions_count=total_transactions_count,
        expense_labels=expense_labels,
        expense_amounts=expense_amounts,
        income_monthly=income_monthly,
        expense_monthly=expense_monthly,
        months=months,
        month_display_labels=month_display_labels
    )

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add a new transaction."""
    if request.method == "POST":
        t_type = request.form.get("type", "").strip().lower()
        category = request.form.get("category", "").strip().lower()
        amount_raw = request.form.get("amount", "").strip()
        t_date = request.form.get("date", "").strip()
        note = request.form.get("note", "").strip()

        if t_type not in ["income", "expense"]:
            flash("Please choose a valid transaction type.", "danger")
            return render_template("add.html")

        if not category:
            flash("Please select a category.", "danger")
            return render_template("add.html")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            flash("Please enter a valid amount greater than zero.", "danger")
            return render_template("add.html")

        if not t_date:
            t_date = date.today().strftime("%Y-%m-%d")

        user_id = session.get("user_id")
        try:
            query_db(
                "INSERT INTO transactions(user_id, type, category, amount, note, date) VALUES(%s, %s, %s, %s, %s, %s)",
                (user_id, t_type, category, amount, note, t_date),
                commit=True
            )
            flash(f"{t_type.capitalize()} of ₹{amount:,.2f} added successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Could not save transaction. Please verify your account and try again.", "danger")
            return render_template("add.html", today=t_date)

    return render_template("add.html", today=date.today().strftime("%Y-%m-%d"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    """Edit an existing transaction."""
    user_id = session["user_id"]
    transaction = query_db(
        "SELECT * FROM transactions WHERE id = %s AND user_id = %s",
        (id, user_id),
        one=True
    )

    if not transaction:
        flash("Transaction not found or you don't have permission to edit it.", "danger")
        return redirect(url_for("history"))

    if request.method == "POST":
        t_type = request.form.get("type", "").strip().lower()
        category = request.form.get("category", "").strip().lower()
        amount_raw = request.form.get("amount", "").strip()
        t_date = request.form.get("date", "").strip()
        note = request.form.get("note", "").strip()

        if t_type not in ["income", "expense"]:
            flash("Please choose a valid transaction type.", "danger")
            return render_template("edit.html", transaction=transaction)

        if not category:
            flash("Please select a category.", "danger")
            return render_template("edit.html", transaction=transaction)

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            flash("Please enter a valid amount greater than zero.", "danger")
            return render_template("edit.html", transaction=transaction)

        if not t_date:
            t_date = date.today().strftime("%Y-%m-%d")

        query_db(
            """
            UPDATE transactions 
            SET type = %s, category = %s, amount = %s, note = %s, date = %s 
            WHERE id = %s AND user_id = %s
            """,
            (t_type, category, amount, note, t_date, id, user_id),
            commit=True
        )

        flash("Transaction updated successfully!", "success")
        return redirect(url_for("history"))

    # Convert date to YYYY-MM-DD string if needed
    t_data = dict(transaction)
    if isinstance(t_data.get("date"), (date, datetime)):
        t_data["date"] = t_data["date"].strftime("%Y-%m-%d")

    return render_template("edit.html", transaction=t_data)

@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    """Delete a transaction."""
    user_id = session["user_id"]
    query_db("DELETE FROM transactions WHERE id = %s AND user_id = %s", (id, user_id), commit=True)
    flash("Transaction deleted successfully.", "info")
    return redirect(request.referrer or url_for("history"))

@app.route("/history", methods=["GET"])
@login_required
def history():
    """Search, filter, sort, and view complete transaction history."""
    user_id = session["user_id"]

    filter_type = request.args.get("type", "").strip().lower()
    filter_category = request.args.get("category", "").strip().lower()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "date_desc").strip()

    # Base query
    query = "SELECT * FROM transactions WHERE user_id = %s"
    params = [user_id]

    if filter_type in ["income", "expense"]:
        query += " AND type = %s"
        params.append(filter_type)

    if filter_category:
        query += " AND LOWER(category) = %s"
        params.append(filter_category)

    if date_from:
        query += " AND date >= %s"
        params.append(date_from)

    if date_to:
        query += " AND date <= %s"
        params.append(date_to)

    if search:
        query += " AND (LOWER(note) LIKE %s OR LOWER(category) LIKE %s)"
        params.append(f"%{search.lower()}%")
        params.append(f"%{search.lower()}%")

    # Sorting
    if sort_by == "date_asc":
        query += " ORDER BY date ASC, id ASC"
    elif sort_by == "amount_desc":
        query += " ORDER BY amount DESC"
    elif sort_by == "amount_asc":
        query += " ORDER BY amount ASC"
    else: # date_desc
        query += " ORDER BY date DESC, id DESC"

    results = query_db(query, tuple(params))

    # Live summary calculations
    summary_income = sum(float(row["amount"] or 0) for row in results if row["type"] == "income")
    summary_expense = sum(float(row["amount"] or 0) for row in results if row["type"] == "expense")
    total_count = len(results)
    net = summary_income - summary_expense

    # Categories list for filter dropdown
    cat_rows = query_db("SELECT DISTINCT category FROM transactions WHERE user_id = %s ORDER BY category ASC", (user_id,))
    available_categories = [r["category"] for r in cat_rows]

    return render_template(
        "history.html",
        results=results,
        summary_income=summary_income,
        summary_expense=summary_expense,
        total_count=total_count,
        net=net,
        available_categories=available_categories,
        filter_type=filter_type,
        filter_category=filter_category,
        date_from=date_from,
        date_to=date_to,
        search=search,
        sort_by=sort_by
    )

@app.route("/export")
@login_required
def export():
    """Export transactions to CSV with currently applied filters."""
    user_id = session["user_id"]

    filter_type = request.args.get("type", "").strip().lower()
    filter_category = request.args.get("category", "").strip().lower()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    search = request.args.get("search", "").strip()

    query = "SELECT * FROM transactions WHERE user_id = %s"
    params = [user_id]

    if filter_type in ["income", "expense"]:
        query += " AND type = %s"
        params.append(filter_type)
    if filter_category:
        query += " AND LOWER(category) = %s"
        params.append(filter_category)
    if date_from:
        query += " AND date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND date <= %s"
        params.append(date_to)
    if search:
        query += " AND (LOWER(note) LIKE %s OR LOWER(category) LIKE %s)"
        params.append(f"%{search.lower()}%")
        params.append(f"%{search.lower()}%")

    query += " ORDER BY date DESC, id DESC"
    transactions = query_db(query, tuple(params))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Type", "Category", "Amount (INR)", "Note"])

    for row in transactions:
        writer.writerow([
            row["id"],
            str(row["date"]),
            row["type"].capitalize(),
            row["category"].capitalize(),
            f"{float(row['amount']):.2f}",
            row["note"] or ""
        ])

    output.seek(0)
    filename = f"paisa_pulse_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)