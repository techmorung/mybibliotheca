from app import create_app

# Create and expose the Flask app for WSGI (Gunicorn will use this)
app = create_app()
