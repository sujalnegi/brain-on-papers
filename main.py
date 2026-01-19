from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Home route - redirects to login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        # Add your authentication logic here
        # For now, we'll just redirect to dashboard
        # In production, verify credentials against database
        
        if email and password:
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please enter valid credentials', 'error')
    
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user' not in session:
        flash('Please login to access the dashboard', 'warning')
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)