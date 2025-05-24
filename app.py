import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///waste_management.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models
    from models import User, WasteItem, Transaction, RecyclingCredit  # noqa: F401
    
    # Create database tables
    db.create_all()
    
    # Import and register routes
    from routes import *  # noqa: F401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
