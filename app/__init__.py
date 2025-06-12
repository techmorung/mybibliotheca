import os
from flask import Flask
from sqlalchemy import inspect
from .models import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Optional: Automatically create tables if DB is empty
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            print("📚 Creating database schema...")
            db.create_all()
        else:
            print("✅ Tables already present.")

    from .routes import bp
    app.register_blueprint(bp)

    return app
