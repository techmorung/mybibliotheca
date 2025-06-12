from app import create_app

# This app is intended to be run via Gunicorn only
app = create_app()