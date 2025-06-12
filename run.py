from app import create_app

# This app is intended to be run via Gunicorn only
app = create_app()
if __name__ == '__main__':
    raise RuntimeError("❌ This app is not meant to be run directly. Use Gunicorn:\n\n    gunicorn -w 4 -b 0.0.0.0:5054 run:app")
