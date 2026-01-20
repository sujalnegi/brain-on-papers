from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth

load_dotenv()

cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print("✓ Firebase Admin SDK initialized successfully")
else:
    print(f"⚠ Warning: Firebase credentials file not found at {cred_path}")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
CORS(app)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    
    firebase_config = {
        'apiKey': os.getenv('FIREBASE_API_KEY'),
        'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
        'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.getenv('FIREBASE_APP_ID'),
        'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
    }
    
    api_key = firebase_config['apiKey']
    if api_key:
        print(f"✓ Firebase API Key loaded: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("✗ Firebase API Key is None or empty!")
    
    return render_template('login.html', firebase_config=firebase_config)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=session['user'])

@app.route('/auth/verify', methods=['POST'])
def verify_auth():
    try:
        id_token = request.json.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'No token provided'}), 400
        
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name', email)
        
        session['user'] = {
            'uid': uid,
            'email': email,
            'name': name
        }
        
        return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200
    
    except Exception as e:
        print(f"Authentication error: {e}")
        return jsonify({'error': str(e)}), 401

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)