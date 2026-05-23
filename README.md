# 💰 Paisa Pulse - Personal Finance Tracker
Python | Flask | PostgreSQL

> Track your money, understand your habits.

Built by Siddharth Mishra

---

## 🎯 The Problem

Most people have no clear picture of where their money goes. Generic banking apps show 
transactions but offer little insight. Common problems:

- No visual breakdown of spending habits
- No way to compare spending across months
- Raw transaction lists with no actionable insights
- No easy way to export or analyze your own data

## 💡 The Solution

Paisa Pulse is a personal finance tracker that lets you log every income and expense, 
visualize your spending patterns with charts, and receive auto-generated insights about 
your financial habits — all in a clean, simple web interface.

🔗 **Live Demo:** [your-render-url.onrender.com](https://your-render-url.onrender.com)

---

## ✨ Features

### 🔐 User Authentication
- Secure registration and login
- Password hashing with Werkzeug
- Session-based authentication

### 📊 Dashboard
- **Summary Cards** — Total balance, income, and expenses at a glance
- **Doughnut Chart** — Visual breakdown of spending by category (Food, Rent, Transport etc.)
- **Bar Chart** — 6-month income vs expense trend
- **Monthly Insights** — Auto-generated text insights like:
  - "You saved ₹8,000 this month"
  - "Your biggest expense is Food at ₹3,200 (42% of expenses)"
  - "You're overspending compared to last month by ₹1,500"
- **Recent Transactions** — Last 5 transactions at a glance

### ➕ Add Transactions
- Log income or expenses with category, amount, date, and optional notes
- Dynamic category dropdown — changes based on income or expense type
- Instant redirect to dashboard with success confirmation

### 📋 Transaction History
- Full transaction table with all records
- Filter by type, category, and date range
- Live summary bar showing filtered totals
- Color-coded rows — green for income, red for expenses
- Delete any transaction with one click

### 📤 CSV Export
- Download all transactions as a .csv file
- Compatible with Excel and Google Sheets

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| Backend | Flask (Python) |
| Database | PostgreSQL |
| Authentication | Werkzeug security |
| Frontend | Jinja2 templates, Bootstrap 5 |
| Charts | Chart.js |
| Deployment | Render.com |

---

## 💡 The Insights Engine

The monthly insight card auto-generates observations using simple but effective logic:

```python
# Biggest expense category
biggest = max(expense_by_category, key=lambda row: row["amount"])
percentage = round((biggest_amount / this_month_expense) * 100)

# Savings this month
saved = this_month_income - this_month_expense

# Overspending vs last month
overspending = this_month_expense - last_month_expense
```

Just 3 calculations in Python — but it reads like a smart financial assistant when 
you demo it.

---

## 📁 Project Structure
paisa-pulse/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
└── templates/
├── layout.html        # Base template with Bootstrap navbar
├── index.html         # Landing page
├── register.html      # Registration form
├── login.html         # Login form
├── dashboard.html     # Main dashboard with charts and insights
├── add.html           # Add transaction form
└── history.html       # Full transaction history with filters

---

## 🗄️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);

-- Transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT,
    date DATE NOT NULL
);
```

---

## 🚀 How to Run Locally

**Prerequisites**
- Python 3.8+
- PostgreSQL database (or use the live demo)

**Installation**

1. Clone the repository
git clone https://github.com/sidddev006/paisa-pulse.git
cd paisa-pulse

2. Install dependencies
pip install -r requirements.txt

3. Set your database URL
   
   Create a `.env` file and add:
DATABASE_URL=your_postgresql_url_here

4. Run the application
python app.py

5. Open in browser
http://localhost:5000

---

## 🎯 User Journey

1. **Register/Login** → Create account with secure password hashing
2. **Add Transactions** → Log income and expenses with category and notes
3. **Dashboard** → View charts, insights, and recent transactions
4. **History** → Filter and browse all transactions
5. **Export** → Download data as CSV for further analysis
6. **Logout** → Secure session clearing

---

## 🧠 Technical Challenges Solved

### 1. Dynamic SQL Filtering
**Problem:** History page needed to support multiple optional filters 
simultaneously — type, category, and date range in any combination.

**Solution:** Built the SQL query incrementally, appending `AND` clauses only 
when a filter value is present. This keeps the query clean and avoids 
over-fetching.

### 2. Monthly Data Aggregation
**Problem:** Bar chart needed income and expense totals grouped by month for 
the last 6 months, with zero values for months with no transactions.

**Solution:** Used PostgreSQL's `TO_CHAR` for date formatting and `GROUP BY` 
month and type, then mapped results into two dictionaries. JavaScript fills 
in missing months with 0.

### 3. SQLite to PostgreSQL Migration
**Problem:** SQLite works locally but Render.com doesn't support persistent 
SQLite files in production.

**Solution:** Migrated to PostgreSQL — updated all `?` placeholders to `%s`, 
replaced `strftime` with `TO_CHAR`, and used `psycopg2` with `DictCursor` 
for dictionary-style row access.

---

## 📚 What I Learned

**Technical Skills**
- Building full-stack web applications with Flask
- Database design and SQL queries
- Data visualization with Chart.js
- Migrating from SQLite to PostgreSQL for production
- Deploying Flask apps on Render.com
- Session management and authentication

**Problem-Solving**
- Debugging database query issues across environments
- Handling edge cases in financial calculations (empty months, zero expenses)
- Managing state across routes with GET parameters

---

## 🔮 Future Enhancements
- [ ] Budget goals — set monthly limits per category with alerts
- [ ] Dark mode
- [ ] PDF export
- [ ] Recurring transactions
- [ ] Multi-currency support

---

## 💭 Development Notes

This project was built independently with AI used as a Socratic tutor — 
asking guiding questions rather than providing direct answers. The database 
design, route logic, SQL queries, and insight calculations were all reasoned 
through and written by me.

---

## 🙏 Acknowledgments

- Bootstrap & Chart.js for the frontend frameworks
- Render.com for hosting
- AI assistance for guided learning and debugging support

---

## 👤 Author

Siddharth Mishra
GitHub: @sidddev006

---

📬 Questions or feedback? Feel free to reach out via GitHub!

This is Paisa Pulse. Track your money, understand your habits. 💰
