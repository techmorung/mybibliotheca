import os
from flask import Flask
from sqlalchemy import inspect
from .models import db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SECRET_KEY_HERE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # ✅ Robust schema check inside app context
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.get_table_names():  # No tables in DB
            print("📚 Creating database schema...")
            db.create_all()
        else:
            print("✅ Tables already present.")

    from .routes import bp
    app.register_blueprint(bp)

    return app
