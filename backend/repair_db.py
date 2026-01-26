from app.db.db import init_db
print("Running init_db manually...")
try:
    init_db()
    print("Database initialized successfully.")
except Exception as e:
    print(f"Error: {e}")
