import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'

    # Use Docker database path if explicitly set, otherwise default to local development path
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'books.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ISBN_API_KEY = os.environ.get('ISBN_API_KEY') or 'your_isbn_api_key'
    TIMEZONE = os.environ.get('TIMEZONE') or 'UTC'
