from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'user', 'recycler'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    waste_items = db.relationship('WasteItem', foreign_keys='WasteItem.user_id', backref='user', lazy=True)
    collected_items = db.relationship('WasteItem', foreign_keys='WasteItem.recycler_id', backref='recycler', lazy=True)
    recycling_credits = db.relationship('RecyclingCredit', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_total_credits(self):
        return sum(credit.amount for credit in self.recycling_credits)
    
    def __repr__(self):
        return f'<User {self.username}>'

class WasteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qr_code = db.Column(db.String(256), unique=True, nullable=False)
    waste_type = db.Column(db.String(50), nullable=False)  # 'plastic', 'metal', 'paper', etc.
    weight = db.Column(db.Float, default=0.0)  # estimated weight in kg
    blockchain_hash = db.Column(db.String(256))  # hash of the transaction on blockchain
    status = db.Column(db.String(20), default='created')  # 'created', 'collected', 'processed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    collected_at = db.Column(db.DateTime)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recycler_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    transactions = db.relationship('Transaction', backref='waste_item', lazy=True)
    
    def __repr__(self):
        return f'<WasteItem {self.id} - {self.waste_type}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # 'created', 'collected', 'processed'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    blockchain_hash = db.Column(db.String(256))
    
    # Foreign keys
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.action}>'

class RecyclingCredit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    blockchain_hash = db.Column(db.String(256))
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id'))
    
    def __repr__(self):
        return f'<RecyclingCredit {self.id} - {self.amount}>'
