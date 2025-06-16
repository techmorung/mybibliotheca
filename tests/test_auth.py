import pytest
from flask import url_for

class TestAuthentication:
    """Test authentication functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data

    def test_register_page_loads(self, client):
        """Test that registration page loads correctly."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data

    def test_user_registration(self, client, app):
        """Test user registration process."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password2': 'password123',
            'submit': 'Register'
        })
        assert response.status_code == 302  # Redirect after successful registration
        
        # Check if user was created
        with app.app_context():
            from app.models import User
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'

    def test_user_login(self, client, regular_user):
        """Test user login process."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123',
            'submit': 'Sign In'
        })
        assert response.status_code == 302  # Redirect after successful login

    def test_login_with_wrong_password(self, client, regular_user):
        """Test login with incorrect password."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
            'submit': 'Sign In'
        })
        assert response.status_code == 200  # Stay on login page
        assert b'Invalid username/email or password' in response.data

    def test_logout(self, client, regular_user):
        """Test user logout."""
        # First login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Then logout
        response = client.get('/auth/logout')
        assert response.status_code == 302  # Redirect after logout

    def test_protected_route_requires_login(self, client):
        """Test that protected routes require authentication."""
        response = client.get('/add')
        assert response.status_code == 302  # Redirect to login
        assert '/auth/login' in response.location

class TestUserDataSeparation:
    """Test that users can only see their own data."""
    
    def test_users_see_only_their_books(self, client, app):
        """Test that users only see books they own."""
        # Create two users with books
        with app.app_context():
            from app.models import User, Book, db
            
            user1 = User(username='user1', email='user1@test.com')
            user1.set_password('pass123')
            user2 = User(username='user2', email='user2@test.com')
            user2.set_password('pass123')
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            book1 = Book(title='User1 Book', author='Author1', isbn='111', user_id=user1.id)
            book2 = Book(title='User2 Book', author='Author2', isbn='222', user_id=user2.id)
            
            db.session.add(book1)
            db.session.add(book2)
            db.session.commit()
        
        # Login as user1 and check they only see their book
        client.post('/auth/login', data={'username': 'user1', 'password': 'pass123'})
        response = client.get('/')
        assert b'User1 Book' in response.data
        assert b'User2 Book' not in response.data
        
        # Logout and login as user2
        client.get('/auth/logout')
        client.post('/auth/login', data={'username': 'user2', 'password': 'pass123'})
        response = client.get('/')
        assert b'User2 Book' in response.data
        assert b'User1 Book' not in response.data
