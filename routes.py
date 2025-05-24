from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid
import json

from app import app, db
from models import User, WasteItem, Transaction, RecyclingCredit
from waste_classifier import classify_waste
from blockchain import generate_blockchain_hash, create_token_transaction

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user.role == 'admin':
                    next_page = url_for('admin_dashboard')
                elif user.role == 'recycler':
                    next_page = url_for('recycler_dashboard')
                else:
                    next_page = url_for('user_dashboard')
                    
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Validate role
        if role not in ['user', 'recycler']:
            flash('Invalid role selected', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Dashboard routes based on user role
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'recycler':
        return redirect(url_for('recycler_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

# User routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get user stats
    waste_items = WasteItem.query.filter_by(user_id=current_user.id).all()
    total_credits = current_user.get_total_credits()
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    waste_types = {}
    for item in waste_items:
        waste_types[item.waste_type] = waste_types.get(item.waste_type, 0) + 1
    
    return render_template('user/dashboard.html', 
                          waste_items=waste_items,
                          total_credits=total_credits,
                          recent_transactions=recent_transactions,
                          waste_types=waste_types)

@app.route('/user/scan', methods=['GET', 'POST'])
@login_required
def user_scan():
    if current_user.role != 'user':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('user/scan.html')

@app.route('/user/classify', methods=['POST'])
@login_required
def classify_waste_item():
    if current_user.role != 'user':
        return jsonify({'error': 'Access denied'}), 403
    
    image_data = request.json.get('image')
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400
    
    # Classify waste using our ML model
    waste_type, confidence = classify_waste(image_data)
    
    return jsonify({
        'waste_type': waste_type,
        'confidence': confidence
    })

@app.route('/user/generate_qr', methods=['POST'])
@login_required
def generate_qr():
    if current_user.role != 'user':
        return jsonify({'error': 'Access denied'}), 403
    
    waste_type = request.json.get('waste_type')
    if not waste_type:
        return jsonify({'error': 'No waste type provided'}), 400
    
    # Generate unique QR code
    qr_code = str(uuid.uuid4())
    
    # Create waste item entry
    waste_item = WasteItem(
        qr_code=qr_code,
        waste_type=waste_type,
        user_id=current_user.id,
        blockchain_hash=generate_blockchain_hash()
    )
    
    # Create transaction record
    transaction = Transaction(
        action='created',
        user_id=current_user.id,
        waste_item=waste_item,
        blockchain_hash=generate_blockchain_hash()
    )
    
    db.session.add(waste_item)
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'qr_code': qr_code,
        'waste_type': waste_type
    })

@app.route('/user/history')
@login_required
def user_history():
    if current_user.role != 'user':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    waste_items = WasteItem.query.filter_by(user_id=current_user.id).order_by(WasteItem.created_at.desc()).all()
    
    return render_template('user/history.html', waste_items=waste_items)

# Recycler routes
@app.route('/recycler/dashboard')
@login_required
def recycler_dashboard():
    if current_user.role != 'recycler':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get recycler stats
    collected_items = WasteItem.query.filter_by(recycler_id=current_user.id).all()
    recent_collections = WasteItem.query.filter_by(recycler_id=current_user.id).order_by(WasteItem.collected_at.desc()).limit(5).all()
    
    waste_types = {}
    for item in collected_items:
        waste_types[item.waste_type] = waste_types.get(item.waste_type, 0) + 1
    
    return render_template('recycler/dashboard.html', 
                          collected_items=collected_items,
                          recent_collections=recent_collections,
                          waste_types=waste_types)

@app.route('/recycler/scan')
@login_required
def recycler_scan():
    if current_user.role != 'recycler':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('recycler/scan.html')

@app.route('/recycler/verify_qr', methods=['POST'])
@login_required
def verify_qr():
    if current_user.role != 'recycler':
        return jsonify({'error': 'Access denied'}), 403
    
    qr_code = request.json.get('qr_code')
    if not qr_code:
        return jsonify({'error': 'No QR code provided'}), 400
    
    # Verify the QR code
    waste_item = WasteItem.query.filter_by(qr_code=qr_code).first()
    
    if not waste_item:
        return jsonify({'error': 'Invalid QR code'}), 404
    
    if waste_item.status != 'created':
        return jsonify({'error': 'This waste item has already been collected'}), 400
    
    # Update waste item status
    waste_item.status = 'collected'
    waste_item.collected_at = datetime.utcnow()
    waste_item.recycler_id = current_user.id
    
    # Create transaction record
    transaction = Transaction(
        action='collected',
        user_id=current_user.id,
        waste_item=waste_item,
        blockchain_hash=generate_blockchain_hash()
    )
    
    # Award recycling credits to the user
    # Credit amount based on waste type
    credit_mapping = {
        'plastic': 10.0,
        'metal': 15.0,
        'paper': 5.0,
        'glass': 8.0,
        'electronic': 20.0,
        'organic': 3.0,
        'other': 2.0
    }
    
    credit_amount = credit_mapping.get(waste_item.waste_type, 5.0)
    
    # Create blockchain transaction for token
    token_hash = create_token_transaction(waste_item.user_id, credit_amount)
    
    # Create recycling credit record
    recycling_credit = RecyclingCredit(
        amount=credit_amount,
        description=f"Credit for recycling {waste_item.waste_type}",
        user_id=waste_item.user_id,
        waste_item_id=waste_item.id,
        blockchain_hash=token_hash
    )
    
    db.session.add(transaction)
    db.session.add(recycling_credit)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'waste_type': waste_item.waste_type,
        'user_id': waste_item.user_id,
        'credits_awarded': credit_amount
    })

@app.route('/recycler/history')
@login_required
def recycler_history():
    if current_user.role != 'recycler':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    collected_items = WasteItem.query.filter_by(recycler_id=current_user.id).order_by(WasteItem.collected_at.desc()).all()
    
    return render_template('recycler/history.html', collected_items=collected_items)

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get system stats
    total_users = User.query.filter_by(role='user').count()
    total_recyclers = User.query.filter_by(role='recycler').count()
    total_waste_items = WasteItem.query.count()
    processed_items = WasteItem.query.filter_by(status='collected').count()
    
    # Calculate processing rate
    processing_rate = (processed_items / total_waste_items * 100) if total_waste_items > 0 else 0
    
    # Get waste type distribution
    waste_items = WasteItem.query.all()
    waste_types = {}
    for item in waste_items:
        waste_types[item.waste_type] = waste_types.get(item.waste_type, 0) + 1
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          total_recyclers=total_recyclers,
                          total_waste_items=total_waste_items,
                          processed_items=processed_items,
                          processing_rate=processing_rate,
                          waste_types=waste_types,
                          recent_transactions=recent_transactions)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.filter_by(role='user').all()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/recyclers')
@login_required
def admin_recyclers():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    recyclers = User.query.filter_by(role='recycler').all()
    
    return render_template('admin/recyclers.html', recyclers=recyclers)

@app.route('/admin/transactions')
@login_required
def admin_transactions():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    
    return render_template('admin/transactions.html', transactions=transactions)

# Create initial admin user
@app.route('/setup', methods=['GET'])
def setup():
    # Check if admin user already exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        return 'Admin user created successfully. Username: admin@example.com, Password: admin123'
    else:
        return 'Admin user already exists'
