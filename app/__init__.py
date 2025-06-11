import os
from flask import Flask
from .models import db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SECRET_KEY_HERE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # === Auto-create DB if missing ===
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        print(f"📚 Creating new database at {db_path}")
        with app.app_context():
            db.create_all()
    else:
        print(f"✅ Using existing database at {db_path}")

    from .routes import bp
    app.register_blueprint(bp)

    return app
