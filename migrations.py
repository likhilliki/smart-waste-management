from app import app, db
from models import User, WasteItem, Transaction, RecyclingCredit
import sqlalchemy as sa
from sqlalchemy.schema import Column

def migrate_database():
    """Add new columns to User table for wallet integration"""
    with app.app_context():
        # Get database connection
        conn = db.engine.connect()
        
        # Check if wallet_address column exists
        result = conn.execute(sa.text(
            "SELECT name FROM pragma_table_info('user') WHERE name = 'wallet_address'"
        ))
        
        wallet_columns_exist = result.fetchone() is not None
        
        if not wallet_columns_exist:
            print("Adding wallet columns to User table...")
            
            # Add wallet columns
            conn.execute(sa.text(
                "ALTER TABLE user ADD COLUMN wallet_address VARCHAR(256)"
            ))
            conn.execute(sa.text(
                "ALTER TABLE user ADD COLUMN wallet_type VARCHAR(50)"
            ))
            conn.execute(sa.text(
                "ALTER TABLE user ADD COLUMN wallet_linked_at DATETIME"
            ))
            conn.execute(sa.text(
                "ALTER TABLE user ADD COLUMN wallet_verified BOOLEAN DEFAULT 0"
            ))
            
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Wallet columns already exist. No migration needed.")
        
        conn.close()

if __name__ == "__main__":
    migrate_database()