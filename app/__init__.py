from flask import Flask
from .models import db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SECRET_KEY_HERE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app