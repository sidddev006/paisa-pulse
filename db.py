import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g
import logging

logger = logging.getLogger(__name__)

def get_database_url():
    """Retrieve and sanitize DATABASE_URL from environment."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return None
    # Strip any accidental wrapping quotes
    if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
        url = url[1:-1].strip()
    # Normalize postgres:// to postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url if url else None

def test_postgres_connection(url):
    """Test if PostgreSQL connection succeeds."""
    try:
        conn = psycopg2.connect(url, connect_timeout=4)
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"PostgreSQL connection test failed: {e}")
        return False

# Determine DB type at startup or dynamically
_CACHED_DB_TYPE = None

def detect_db_type():
    global _CACHED_DB_TYPE
    if _CACHED_DB_TYPE is not None:
        return _CACHED_DB_TYPE
    url = get_database_url()
    if url and test_postgres_connection(url):
        _CACHED_DB_TYPE = "postgresql"
    else:
        _CACHED_DB_TYPE = "sqlite"
    return _CACHED_DB_TYPE

def get_db():
    """Get active database connection stored in Flask g context."""
    if "db" not in g:
        db_type = detect_db_type()
        if db_type == "postgresql":
            url = get_database_url()
            try:
                g.db = psycopg2.connect(url, cursor_factory=RealDictCursor)
                g.db_type = "postgresql"
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL ({e}), falling back to SQLite.")
                g.db = sqlite3.connect("finance.db")
                g.db.row_factory = sqlite3.Row
                g.db_type = "sqlite"
        else:
            g.db = sqlite3.connect("finance.db")
            g.db.row_factory = sqlite3.Row
            g.db_type = "sqlite"
    return g.db

def close_db(e=None):
    """Close active database connection."""
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

def query_db(query, args=(), one=False, commit=False):
    """
    Execute SQL query agnostic of engine (PostgreSQL vs SQLite).
    Queries are written using standard '%s' placeholders.
    Returns list of dicts (or single dict if one=True), or True / lastrowid on commit.
    """
    db = get_db()
    db_type = getattr(g, "db_type", detect_db_type())

    if db_type == "sqlite":
        # SQLite uses '?' placeholders instead of '%s'
        adapted_query = query.replace("%s", "?")
        cur = db.cursor()
        cur.execute(adapted_query, args)
        if commit:
            db.commit()
            last_id = cur.lastrowid
            cur.close()
            return last_id
        rv = cur.fetchall()
        cur.close()
        # Convert sqlite3.Row to regular dicts with lowercase keys
        results = [{k.lower(): row[k] for k in row.keys()} for row in rv]
        return (results[0] if results else None) if one else results
    else:
        cur = db.cursor()
        cur.execute(query, args)
        if commit:
            db.commit()
            cur.close()
            return True
        rv = cur.fetchall()
        cur.close()
        results = [{k.lower(): row[k] for k in row.keys()} for row in rv]
        return (results[0] if results else None) if one else results

def init_db():
    """Create necessary database tables and indexes."""
    db_type = detect_db_type()
    if db_type == "postgresql":
        url = get_database_url()
        try:
            conn = psycopg2.connect(url, connect_timeout=4)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    hash TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL,
                    note TEXT,
                    date DATE NOT NULL
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
                ON transactions(user_id, date);
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Initialized PostgreSQL database tables.")
            return "postgresql"
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}. Falling back to SQLite.")
            pass

    # SQLite fallback
    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
        ON transactions(user_id, date);
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Initialized SQLite database tables.")
    return "sqlite"
