from flask import Flask, render_template, request, redirect, url_for, session
import random
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def init_db():
    if not os.path.exists('database.db'):
        with sqlite3.connect('database.db') as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS predictions (
                                id INTEGER PRIMARY KEY,
                                user_color TEXT,
                                predicted_color TEXT,
                                correct INTEGER
                            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS admin (
                                username TEXT PRIMARY KEY,
                                password TEXT
                            )''')
            conn.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))

def get_random_color():
    return "#" + ''.join(random.choices('0123456789ABCDEF', k=6))

def insert_prediction(user_color, predicted_color, correct):
    with sqlite3.connect('database.db') as conn:
        conn.execute("INSERT INTO predictions (user_color, predicted_color, correct) VALUES (?, ?, ?)", (user_color, predicted_color, correct))

def get_all_predictions():
    with sqlite3.connect('database.db') as conn:
        return conn.execute("SELECT * FROM predictions").fetchall()

@app.route('/')
def home():
    return '''
    <html><head><title>Color Predictor</title></head><body style="font-family:sans-serif;text-align:center;padding:40px">
    <h2>Pick a Color</h2>
    <form method="POST" action="/predict">
        <input type="color" name="color" value="#000000">
        <button type="submit">Predict</button>
    </form>
    </body></html>
    '''

@app.route('/predict', methods=['POST'])
def predict():
    user_color = request.form['color']
    predicted_color = get_random_color()
    correct = int(user_color.lower() == predicted_color.lower())
    insert_prediction(user_color, predicted_color, correct)
    session['score'] = session.get('score', 0) + correct
    return f'''
    <html><head><title>Prediction Result</title></head><body style="font-family:sans-serif;text-align:center;padding:40px">
    <h2>Prediction Result</h2>
    <p><strong>Your Color:</strong> <span style="color:{user_color}">{user_color}</span></p>
    <p><strong>Predicted Color:</strong> <span style="color:{predicted_color}">{predicted_color}</span></p>
    <p>{'✅ Correct!' if correct else '❌ Incorrect!'}</p>
    <p><strong>Your Score:</strong> {session['score']}</p>
    <a href="/">Try Again</a>
    </body></html>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            user = conn.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                session['admin'] = True
                return redirect(url_for('admin_dashboard'))
    return '''
    <html><head><title>Admin Login</title></head><body style="font-family:sans-serif;text-align:center;padding:40px">
    <h2>Admin Login</h2>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
    </body></html>
    '''

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    predictions = get_all_predictions()
    table_rows = ''.join([f"<tr><td>{p[0]}</td><td>{p[1]}</td><td>{p[2]}</td><td>{'Yes' if p[3] else 'No'}</td></tr>" for p in predictions])
    return f'''
    <html><head><title>Admin Dashboard</title></head><body style="font-family:sans-serif;padding:40px">
    <h2>Admin Dashboard</h2>
    <table border="1" cellpadding="10">
        <tr><th>ID</th><th>User Color</th><th>Predicted Color</th><th>Correct</th></tr>
        {table_rows}
    </table><br>
    <a href="/admin/logout">Logout</a>
    </body></html>
    '''

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)