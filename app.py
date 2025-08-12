from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import nlpcloud

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Dummy database
database = {}

# NLPCloud client setup
def get_client():
    return nlpcloud.Client(
        "finetuned-llama-3-70b",
        os.getenv("NLPCLOUD_API_KEY"),
        gpu=True
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if email in database:
            flash('Email already registered!')
        else:
            database[email] = [name, password]
            flash('Registration successful. Please login.')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in database and check_password_hash(database[email][1], password):
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        if email in database:
            flash('Password reset feature is disabled for demo.')
        else:
            flash('Email not found.')
    return render_template('forgot.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    result = None
    if request.method == 'POST':
        task = request.form['task']
        text = request.form['text']
        client = get_client()

        try:
            if task == 'ner':
                entity = request.form['entity']
                response = client.entities(text, searched_entity=entity)
                result = response

            elif task == 'summarization':
                response = client.summarization(text)
                result = response

            elif task == 'sentiment':
                response = client.sentiment(text)
                scores = response['scored_labels']
                scores.sort(key=lambda x: x['score'], reverse=True)
                result = f"Sentiment: {scores[0]['label']}"

        except Exception as e:
            flash(f"Error: {e}")

    return render_template('dashboard.html', user=session['user'], result=result)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
