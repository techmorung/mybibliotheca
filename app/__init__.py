import os
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import inspect, text
from .models import db, User
from config import Config

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Handle schema migration with new user tables
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            print("📚 Creating fresh database schema...")
            db.create_all()
        else:
            print("✅ Tables present, checking for migrations...")
            
            # Check for user table (new in v2)
            if 'user' not in existing_tables:
                print("🔄 Adding user authentication tables...")
                db.create_all()
                print("✅ User tables created.")
            
            # Check for new columns in book table
            if 'book' in existing_tables:
                try:
                    columns = [column['name'] for column in inspector.get_columns('book')]
                    
                    # Check for user_id column (critical for v2)
                    if 'user_id' not in columns:
                        print("🔄 Adding user_id to book table...")
                        with db.engine.connect() as conn:
                            # Add user_id column as nullable first
                            conn.execute(text("ALTER TABLE book ADD COLUMN user_id INTEGER"))
                            # We'll handle data migration separately
                            conn.commit()
                        print("✅ user_id column added to book table.")
                    
                    # Check for other missing columns
                    new_columns = ['description', 'published_date', 'page_count', 'categories', 
                                 'publisher', 'language', 'average_rating', 'rating_count', 'created_at']
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
                                elif col_name == 'created_at':
                                    conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} DATETIME"))
                                else:  # description
                                    conn.execute(text(f"ALTER TABLE book ADD COLUMN {col_name} TEXT"))
                            conn.commit()
                        print("✅ Schema migration completed.")
                        
                except Exception as e:
                    print(f"⚠️  Schema migration failed: {e}")
                    print("📚 Creating fresh database schema...")
                    db.create_all()
            
            # Check for reading_log table updates
            if 'reading_log' in existing_tables:
                try:
                    columns = [column['name'] for column in inspector.get_columns('reading_log')]
                    if 'user_id' not in columns:
                        print("🔄 Adding user_id to reading_log table...")
                        with db.engine.connect() as conn:
                            conn.execute(text("ALTER TABLE reading_log ADD COLUMN user_id INTEGER"))
                            conn.execute(text("ALTER TABLE reading_log ADD COLUMN created_at DATETIME"))
                            conn.commit()
                        print("✅ reading_log table updated.")
                except Exception as e:
                    print(f"⚠️  Reading log migration failed: {e}")

    # Register blueprints
    from .routes import bp
    from .auth import auth
    from .admin import admin
    app.register_blueprint(bp)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')

    return app
