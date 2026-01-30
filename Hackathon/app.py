from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
import joblib
import json
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Change this in production

# Load the model and vectorizer
model = joblib.load("models/mental_health_model.pkl")
vectorizer = joblib.load("models/vectorizer (1).pkl")

USER_FILE = "data/users.json"
CHAT_HISTORY_DIR = "data/chat_history"
PROFILE_DIR = "data/profiles"

# Ensure directories exist
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return {}

def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def get_user_chat_file(username):
    return os.path.join(CHAT_HISTORY_DIR, f"{username}_chat_history.json")

def get_user_profile_file(username):
    return os.path.join(PROFILE_DIR, f"{username}_profile.json")

def load_user_chat_history(username):
    chat_file = get_user_chat_file(username)
    if not os.path.exists(chat_file):
        return []
    try:
        with open(chat_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def save_user_chat_history(username, chat_history):
    chat_file = get_user_chat_file(username)
    with open(chat_file, "w") as f:
        json.dump(chat_history, f, indent=2)

def load_user_profile(username):
    profile_file = get_user_profile_file(username)
    if not os.path.exists(profile_file):
        # Create default profile
        profile = {
            "username": username,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_sessions": 0,
            "total_messages": 0,
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_user_profile(username, profile)
        return profile
    try:
        with open(profile_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {
            "username": username,
            "created_date": "Unknown",
            "total_sessions": 0,
            "total_messages": 0,
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def save_user_profile(username, profile):
    profile_file = get_user_profile_file(username)
    with open(profile_file, "w") as f:
        json.dump(profile, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users = load_users()
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['username'] = username

            # Load user's chat history into session
            chat_history = load_user_chat_history(username)
            session['chat_history'] = chat_history

            # Update profile last active
            profile = load_user_profile(username)
            profile['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_user_profile(username, profile)

            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users = load_users()
        if username in users:
            flash('Username already exists.', 'error')
        else:
            users[username] = password
            save_users(users)

            # Create user profile
            profile = {
                "username": username,
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_sessions": 0,
                "total_messages": 0,
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_user_profile(username, profile)

            # Initialize empty chat history
            save_user_chat_history(username, [])

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username and 'chat_history' in session:
        # Save final chat history before logout
        save_user_chat_history(username, session['chat_history'])

        # Update profile last active
        profile = load_user_profile(username)
        profile['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_user_profile(username, profile)

    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

from collections import namedtuple

# Create a simple profile object
Profile = namedtuple('Profile', ['username', 'created_date', 'total_sessions', 'total_messages', 'last_active'])

@app.route('/profile')
@login_required
def profile():
    username = session.get('username')
    if not username:
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))

    # Load user profile
    profile_data = load_user_profile(username)

    # Create profile object
    profile_obj = Profile(
        username=profile_data.get('username', username),
        created_date=profile_data.get('created_date', 'Unknown'),
        total_sessions=profile_data.get('total_sessions', 0),
        total_messages=profile_data.get('total_messages', 0),
        last_active=profile_data.get('last_active', 'Unknown')
    )

    # Load chat history for display
    chat_history = load_user_chat_history(username)

    # For now, we'll show all messages as one session
    chat_sessions = []
    if chat_history:
        chat_sessions.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'messages': chat_history
        })

    return render_template('profile.html', profile=profile_obj, chat_history=chat_sessions)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/chat')
@login_required
def chat_page():
    # Initialize chat history if not exists
    if 'chat_history' not in session:
        username = session.get('username')
        if username:
            chat_history = load_user_chat_history(username)
            session['chat_history'] = chat_history
        else:
            session['chat_history'] = []
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'response': 'Please enter a message.'})

    username = session.get('username')
    if not username:
        return jsonify({'response': 'Session error. Please log in again.'})

    # Initialize chat history if not exists
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Vectorize the input
    X = vectorizer.transform([user_message])

    # Get prediction
    response = model.predict(X)[0]

    # Add messages to history with timestamp
    timestamp = datetime.now().strftime('%H:%M')
    session['chat_history'].append({'type': 'user', 'message': user_message, 'timestamp': timestamp})
    session['chat_history'].append({'type': 'bot', 'message': response, 'timestamp': timestamp})

    # Keep only last 50 messages in session to prevent bloat
    if len(session['chat_history']) > 50:
        session['chat_history'] = session['chat_history'][-50:]

    # Save to persistent storage
    save_user_chat_history(username, session['chat_history'])

    # Update profile statistics
    profile = load_user_profile(username)
    profile['total_messages'] = profile.get('total_messages', 0) + 2  # +2 for user and bot messages
    profile['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_user_profile(username, profile)

    session.modified = True

    return jsonify({'response': response})

@app.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    username = session.get('username')
    if username:
        session['chat_history'] = []
        save_user_chat_history(username, [])
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'})

if __name__ == '__main__':
    app.run(debug=True)
