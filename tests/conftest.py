import pytest
import os
import tempfile
from app import create_app
from app.models import db, User, Book, ReadingLog

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the test database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        admin = User(
            username='admin',
            email='admin@test.com',
            is_admin=True,
            is_active=True  # Explicitly set for testing
        )
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        # Refresh the user to avoid detached instance issues
        db.session.refresh(admin)
        return admin

@pytest.fixture
def regular_user(app):
    """Create a regular user for testing."""
    with app.app_context():
        user = User(
            username='testuser',
            email='user@test.com',
            is_admin=False,
            is_active=True  # Explicitly set for testing
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        # Refresh the user to avoid detached instance issues
        db.session.refresh(user)
        return user

@pytest.fixture
def sample_book(app, regular_user):
    """Create a sample book for testing."""
    with app.app_context():
        book = Book(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            user_id=regular_user.id
        )
        db.session.add(book)
        db.session.commit()
        return book
