# 💸 Paisa Pulse — Smart Personal Finance Tracker

[![Flask](https://img.shields.io/badge/Framework-Flask%203.x-emerald)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Supabase-336791)](https://supabase.com/)
[![TailwindCSS](https://img.shields.io/badge/Design-Tailwind%20CSS-38bdf8)](https://tailwindcss.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-46e3b7)](https://render.com/)

> **Paisa Pulse** is a modern, responsive personal finance and wealth management web application built with Python (Flask), PostgreSQL (Supabase / Render), and Tailwind CSS. It empowers users to easily log income & expenses, analyze monthly cash flow with interactive visual charts, filter financial history, and download instant CSV reports.

*Built by **Siddharth Mishra** ([@sidddev006](https://github.com/sidddev006))*

---

## 🎯 The Problem & The Solution

Most people have no clear picture of where their money goes. Generic banking apps show transactions but offer little insight:
- No visual breakdown of spending habits across categories
- No clean way to compare spending across consecutive months
- Raw transaction lists with no actionable or automated insights
- Clunky interfaces and lack of simple data export

**Paisa Pulse** solves this with an intuitive, ultra-fast interface that lets you log every income and expense, visualize your cash flow trends with Chart.js, filter your entire ledger, and receive smart financial alerts.

---

## ✨ Key Features

- **📊 Comprehensive Financial Dashboard**
  - Real-time Total Balance, Income, Expense, and Savings Rate metrics.
  - Interactive **Chart.js** visuals (Category distribution doughnut chart & 6-month monthly cash flow bar chart).
  - Automated financial insights (savings milestone detection, overspending warnings vs previous month, and top expense category analysis).
  - Quick transaction activity feed.

- **➕ Smart Transaction Logging & Editing**
  - Log both **Income** and **Expenses** with intuitive emoji-tagged categories.
  - One-tap quick amount buttons (`+₹100`, `+₹500`, `+₹1,000`, `+₹5,000`, `+₹10,000`).
  - Quick date selectors (`Today`, `Yesterday`).
  - Full **Edit Transaction** support to update past amounts, categories, dates, or notes.

- **🔍 Advanced Search & Filter Engine**
  - Instant keyword search across notes and categories.
  - Granular filters by Type (`Income` / `Expense`), Category, and Custom Date Ranges.
  - One-click date range presets (`This Month`, `Last 30 Days`, `This Year`).
  - Sorting by Date (Newest/Oldest) and Amount (Highest/Lowest).
  - Live summary statistics for the filtered dataset.

- **📥 One-Click CSV Export**
  - Export your filtered or complete transaction history formatted for spreadsheets (Excel / Google Sheets) and tax preparation.

- **🛡️ Enterprise-Grade Resilience & Security**
  - Dual-engine database adapter: connects seamlessly to **Supabase PostgreSQL** in production and falls back to **SQLite (`finance.db`)** locally if `DATABASE_URL` is unset or unreachable.
  - Automatic table creation and index migration on startup (`users` and `transactions` tables).
  - Cryptographic password hashing (`scrypt`) with secure session cookies.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| **Backend** | Python 3, Flask 3.x, Werkzeug, Gunicorn |
| **Database** | PostgreSQL (Supabase / Render Postgres) with automatic SQLite local fallback |
| **Frontend** | Jinja2 Templates, Tailwind CSS, Bootstrap Icons, Google Fonts (Plus Jakarta Sans & Outfit) |
| **Charts** | Chart.js 4.x (Doughnut & Bar Charts) |
| **Deployment** | Render.com Web Service (`gunicorn app:app`) |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- (Optional) A free [Supabase](https://supabase.com) account or [Render PostgreSQL](https://render.com) instance.

### 2. Installation & Setup
```bash
# Clone the repository
git clone https://github.com/sidddev006/paisa-pulse.git
cd paisa-pulse

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your `.env` variables:
```env
SECRET_KEY=your-custom-secret-key

# Optional: Supabase PostgreSQL URI (If omitted or unreachable, SQLite is used automatically)
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

### 4. Run the Application
```bash
python app.py
```
Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## 🌐 Deploying to Render

1. **Push your code to GitHub**.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your `paisa-pulse` repository.
4. Settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. **Environment Variables**:
   - `SECRET_KEY`: (Generate a random secure string)
   - `DATABASE_URL`: (Paste your Supabase Session Pooler or Render PostgreSQL connection string)
6. Click **Deploy Web Service**!

> **Supabase Tip for Render**: For Render (which uses IPv4), use the **Supabase Session Pooler** connection string (port `5432` or `6543`) from your Supabase Project Settings -> Database -> Connection String.

---

## 📁 Project Structure

```
paisa-pulse/
├── app.py                 # Flask application, routes, controllers, Jinja filters
├── db.py                  # Dual-engine DB adapter (PostgreSQL + SQLite fallback)
├── requirements.txt       # Clean deployment dependencies
├── Procfile               # Render / Gunicorn web server process file
├── render.yaml            # Render Blueprint deployment definition
├── .env.example           # Environment configuration template
├── templates/
│   ├── layout.html        # Modern responsive shell & glassmorphic header
│   ├── index.html         # High-converting SaaS landing page
│   ├── dashboard.html     # Analytics dashboard with Chart.js charts
│   ├── history.html       # Search, filter, sort & CSV export view
│   ├── add.html           # Transaction creation form with emoji picker
│   ├── edit.html          # Transaction edit view
│   ├── login.html         # User authentication sign in
│   └── register.html      # Account creation with validation
```

---

## 👤 Author

**Siddharth Mishra**
- GitHub: [@sidddev006](https://github.com/sidddev006)

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
