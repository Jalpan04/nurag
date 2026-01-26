import sqlite3
import uuid
import datetime
from app.core.config import settings

DB_PATH = "rag_app.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Enable Write-Ahead Logging for better concurrency
    try:
        c.execute("PRAGMA journal_mode=WAL;")
    except Exception as e:
        print(f"Warning: Could not set WAL mode: {e}")
    
    # Threads
    c.execute('''CREATE TABLE IF NOT EXISTS threads (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Messages
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        thread_id TEXT,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(thread_id) REFERENCES threads(id)
    )''')
    
    # Agents (Personas)
    c.execute('''CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT,
        system_prompt TEXT,
        model TEXT,
        is_active INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Documents
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Ensure default agent exists
    c.execute("SELECT count(*) FROM agents")
    if c.fetchone()[0] == 0:
        default_id = str(uuid.uuid4())
        default_prompt = "You are 'Grainy Brain', a helpful, witty, and concise AI assistant. Answer naturally and conversationally."
        c.execute("INSERT INTO agents (id, name, system_prompt, model, is_active) VALUES (?, ?, ?, ?, 1)",
                  (default_id, "Default (Grainy Brain)", default_prompt, settings.CHAT_MODEL))

    conn.commit()
    conn.close()

# Initialize on module load? Or explicitly call.
# Better to call from main.py startup event.
