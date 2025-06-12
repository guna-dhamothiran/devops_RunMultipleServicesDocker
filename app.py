from flask import Flask, request, redirect
import psycopg2
import os
import signal
import sys

app = Flask(__name__)

# Graceful shutdown handler
def handle_shutdown(signum, frame):
    print("Graceful shutdown initiated...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)  # For Ctrl+C too

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DATABASE_HOST'),
        port=os.environ.get('DATABASE_PORT'),
        database=os.environ.get('DATABASE_NAME'),
        user=os.environ.get('DATABASE_USER'),
        password=os.environ.get('DATABASE_PASSWORD')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS info (id SERIAL PRIMARY KEY, name VARCHAR(50));')
    conn.commit()
    cur.close()
    conn.close()

init_db()  # Create table on startup

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM info;')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    formatted_data = "<br>".join([f"{row[0]} - {row[1]}" for row in rows])
    return f"""
    ✅ Connected to Database!<br><br>
    <form action="/add" method="post">
        <input type="text" name="name" placeholder="Enter name" required>
        <input type="submit" value="Add Name">
    </form><br>
    <strong>Data:</strong><br>{formatted_data}
    """

@app.route('/add', methods=['POST'])
def add_name():
    name = request.form['name']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM info WHERE name = %s;", (name,))
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO info (name) VALUES (%s);', (name,))
        conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    # Disable reloader to avoid signal handling issues inside Docker
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
