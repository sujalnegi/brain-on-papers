from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime
import uuid

load_dotenv()

cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✓ Firebase Admin SDK initialized successfully")
else:
    print(f"⚠ Warning: Firebase credentials file not found at {cred_path}")
    db = None

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
    
    boards = []
    if db:
        try:
            # Query boards without ordering first (in case index doesn't exist)
            boards_ref = db.collection('boards').where('userId', '==', session['user']['uid'])
            boards_docs = boards_ref.stream()
            boards_list = [{'id': doc.id, **doc.to_dict()} for doc in boards_docs]
            
            boards_list = [board for board in boards_list if not board.get('deleted', False)]
            
            boards = sorted(boards_list, key=lambda x: x.get('createdAt', datetime.min), reverse=True)
            
            print(f"✓ Fetched {len(boards)} active boards for user {session['user']['uid']}")
        except Exception as e:
            print(f"✗ Error fetching boards: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('dashboard.html', user=session['user'], boards=boards)

@app.route('/trash')
def trash():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    deleted_boards = []
    if db:
        try:
            boards_ref = db.collection('boards').where('userId', '==', session['user']['uid'])
            boards_docs = boards_ref.stream()
            boards_list = [{'id': doc.id, **doc.to_dict()} for doc in boards_docs]
            
            deleted_boards = [board for board in boards_list if board.get('deleted', False)]
            
            deleted_boards = sorted(deleted_boards, key=lambda x: x.get('deletedAt', datetime.min), reverse=True)
            
            print(f"✓ Fetched {len(deleted_boards)} deleted boards for user {session['user']['uid']}")
        except Exception as e:
            print(f"✗ Error fetching deleted boards: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('trash.html', user=session['user'], boards=deleted_boards)

@app.route('/api/boards/create', methods=['POST'])
def create_board():
    if 'user' not in session:
        print("✗ Unauthorized: No user in session")
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db:
        print("✗ Database not initialized")
        return jsonify({'error': 'Database not initialized'}), 500
    
    try:
        data = request.json if request.json else {}
        board_id = str(uuid.uuid4())
        
        base_title = data.get('title', 'Untitled Board')
        unique_title = base_title
        
        existing_boards = db.collection('boards').where('userId', '==', session['user']['uid']).stream()
        existing_titles = [board.to_dict().get('title', '') for board in existing_boards]
        
        if unique_title in existing_titles:
            counter = 2
            while f"{base_title} {counter}" in existing_titles:
                counter += 1
            unique_title = f"{base_title} {counter}"
        
        board_data = {
            'userId': session['user']['uid'],
            'title': unique_title,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'content': data.get('content', ''),
            'thumbnail': data.get('thumbnail', '')
        }
        
        print(f"✓ Creating board '{unique_title}' ({board_id}) for user {session['user']['uid']}")
        db.collection('boards').document(board_id).set(board_data)
        print(f"✓ Board {board_id} created successfully")
        
        return jsonify({
            'success': True,
            'boardId': board_id,
            'redirect': url_for('whiteboard', board_id=board_id)
        }), 200
    
    except Exception as e:
        print(f"✗ Error creating board: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/boards', methods=['GET'])
def get_boards():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db:
        return jsonify({'error': 'Database not initialized'}), 500
    
    try:
        boards_ref = db.collection('boards').where('userId', '==', session['user']['uid']).order_by('createdAt', direction=firestore.Query.DESCENDING)
        boards_docs = boards_ref.stream()
        boards = [{'id': doc.id, **doc.to_dict()} for doc in boards_docs]
        
        return jsonify({'success': True, 'boards': boards}), 200
    
    except Exception as e:
        print(f"Error fetching boards: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/boards/<board_id>/update', methods=['PUT'])
def update_board(board_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db:
        return jsonify({'error': 'Database not initialized'}), 500
    
    try:
        data = request.json if request.json else {}
        
        board_ref = db.collection('boards').document(board_id)
        board_doc = board_ref.get()
        
        if not board_doc.exists:
            return jsonify({'error': 'Board not found'}), 404
        
        board_data = board_doc.to_dict()
        if board_data.get('userId') != session['user']['uid']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        new_title = data.get('title')
        if new_title and new_title != board_data.get('title'):
            existing_boards = db.collection('boards').where('userId', '==', session['user']['uid']).stream()
            existing_titles = [b.to_dict().get('title', '') for b in existing_boards if b.id != board_id]
            
            if new_title in existing_titles:
                base_title = new_title
                counter = 2
                while f"{base_title} {counter}" in existing_titles:
                    counter += 1
                new_title = f"{base_title} {counter}"
        
        update_data = {
            'updatedAt': firestore.SERVER_TIMESTAMP
        }
        
        if new_title:
            update_data['title'] = new_title
        if 'content' in data:
            update_data['content'] = data['content']
        if 'thumbnail' in data:
            update_data['thumbnail'] = data['thumbnail']
        
        board_ref.update(update_data)
        
        print(f"✓ Board {board_id} updated successfully")
        
        return jsonify({
            'success': True,
            'boardId': board_id,
            'title': new_title if new_title else board_data.get('title')
        }), 200
    
    except Exception as e:
        print(f"✗ Error updating board: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/boards/<board_id>/delete', methods=['DELETE'])
def delete_board(board_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db:
        return jsonify({'error': 'Database not initialized'}), 500
    
    try:
        board_ref = db.collection('boards').document(board_id)
        board_doc = board_ref.get()
        
        if not board_doc.exists:
            return jsonify({'error': 'Board not found'}), 404
        
        board_data = board_doc.to_dict()
        if board_data.get('userId') != session['user']['uid']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        board_ref.update({
            'deleted': True,
            'deletedAt': firestore.SERVER_TIMESTAMP
        })
        
        print(f"✓ Board {board_id} moved to trash")
        
        return jsonify({
            'success': True,
            'message': 'Board moved to trash'
        }), 200
    
    except Exception as e:
        print(f"✗ Error deleting board: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/boards/<board_id>/restore', methods=['POST'])
def restore_board(board_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db:
        return jsonify({'error': 'Database not initialized'}), 500
    
    try:
        board_ref = db.collection('boards').document(board_id)
        board_doc = board_ref.get()
        
        if not board_doc.exists:
            return jsonify({'error': 'Board not found'}), 404
        
        board_data = board_doc.to_dict()
        if board_data.get('userId') != session['user']['uid']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        board_ref.update({
            'deleted': False,
            'deletedAt': firestore.DELETE_FIELD
        })
        
        print(f"✓ Board {board_id} restored from trash")
        
        return jsonify({
            'success': True,
            'message': 'Board restored successfully'
        }), 200
    
    except Exception as e:
        print(f"✗ Error restoring board: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/boards/<board_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_board(board_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db:
        return jsonify({'error': 'Database not initialized'}), 500
    
    try:
        board_ref = db.collection('boards').document(board_id)
        board_doc = board_ref.get()
        
        if not board_doc.exists:
            return jsonify({'error': 'Board not found'}), 404
        
        board_data = board_doc.to_dict()
        if board_data.get('userId') != session['user']['uid']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Permanently delete the board
        board_ref.delete()
        
        print(f"✓ Board {board_id} permanently deleted")
        
        return jsonify({
            'success': True,
            'message': 'Board permanently deleted'
        }), 200
    
    except Exception as e:
        print(f"✗ Error permanently deleting board: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/whiteboard')
@app.route('/whiteboard/<board_id>')
def whiteboard(board_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    board_data = None
    if board_id and db:
        try:
            board_ref = db.collection('boards').document(board_id)
            board_doc = board_ref.get()
            if board_doc.exists:
                board_data = {'id': board_doc.id, **board_doc.to_dict()}
        except Exception as e:
            print(f"Error fetching board: {e}")
    
    return render_template('whiteboard.html', user=session['user'], board=board_data)

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
    firebase_config = {
        'apiKey': os.getenv('FIREBASE_API_KEY'),
        'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
        'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.getenv('FIREBASE_APP_ID'),
        'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
    }
    return render_template('logout.html', firebase_config=firebase_config)

@app.route('/logout-complete')
def logout_complete():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)