import pytest
from app.models import User, db

class TestUserModel:
    """Test the User model functionality."""
    
    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()  # Apply defaults without committing
            
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
            assert not user.is_admin  # Default should be False
            assert user.is_active  # Default should be True

    def test_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            user.set_password('secret')
            
            # Password should be hashed, not stored in plain text
            assert user.password_hash != 'secret'
            assert user.check_password('secret')
            assert not user.check_password('wrong')

    def test_user_relationships(self, app, regular_user, sample_book):
        """Test user relationships with books."""
        with app.app_context():
            # Re-query the user to avoid detached instance issues
            user = User.query.filter_by(username='testuser').first()
            assert user is not None
            assert len(user.books) == 1
            assert user.books[0].title == 'Test Book'

    def test_admin_user(self, app, admin_user):
        """Test admin user functionality."""
        with app.app_context():
            # Re-query the user to avoid detached instance issues
            user = User.query.filter_by(username='admin').first()
            assert user is not None
            assert user.is_admin
            assert user.is_active
            assert user.username == 'admin'
