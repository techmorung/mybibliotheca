import os
from flask import Flask
from sqlalchemy import inspect, text
from .models import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Optional: Automatically create tables if DB is empty or handle schema migration
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            print("📚 Creating database schema...")
            db.create_all()
        else:
            print("✅ Tables already present.")
            # Check if new columns exist, if not, add them
            try:
                columns = [column['name'] for column in inspector.get_columns('book')]
                new_columns = ['description', 'published_date', 'page_count', 'categories', 'publisher', 'language', 'average_rating', 'rating_count']
                missing_columns = [col for col in new_columns if col not in columns]
                
                if missing_columns:
                    print(f"🔄 Adding missing columns: {missing_columns}")
                    with db.engine.connect() as conn:
                        for col_name in missing_columns:
                            if col_name in ['page_count', 'rating_count']:
                                conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} INTEGER"))
                            elif col_name == 'average_rating':
                                conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} REAL"))
                            elif col_name in ['categories', 'publisher']:
                                conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} VARCHAR(500)"))
                            elif col_name == 'language':
                                conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} VARCHAR(10)"))
                            elif col_name == 'published_date':
                                conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} VARCHAR(50)"))
                            else:  # description
                                conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} TEXT"))
                        conn.commit()
                    print("✅ Schema migration completed.")
            except Exception as e:
                print(f"⚠️  Schema migration failed: {e}")
                print("📚 Creating fresh database schema...")
                db.create_all()

    from .routes import bp
    app.register_blueprint(bp)

    return app
