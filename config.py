import os

# Get the absolute path to the directory this file lives in
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for session/csrf protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'

    # Absolute path to the SQLite database (so it always works no matter where the app runs)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'books.db')}"

    # Turn off unnecessary tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API key used for ISBN metadata lookups
    ISBN_API_KEY = os.environ.get('ISBN_API_KEY') or 'your_isbn_api_key'
