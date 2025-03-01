"""
Tests for authentication functionality.
"""

import pytest
from flask import session, g
from app.auth.models import User


def test_login_page(client):
    """Test login page loads properly."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_login_success(client, auth):
    """Test successful login."""
    response = auth.login()
    assert response.headers.get('Location') == 'http://localhost/content/dashboard'
    
    with client:
        client.get('/')
        assert session['_user_id'] == '1'


def test_login_incorrect_password(client):
    """Test login with incorrect password."""
    response = client.post(
        '/auth/login',
        data={'username': 'admin', 'password': 'wrongpassword'}
    )
    assert b'Invalid username or password' in response.data


def test_login_invalid_username(client):
    """Test login with non-existent username."""
    response = client.post(
        '/auth/login',
        data={'username': 'nonexistent', 'password': 'password'}
    )
    assert b'Invalid username or password' in response.data


def test_logout(client, auth):
    """Test logout functionality."""
    auth.login()
    
    with client:
        auth.logout()
        assert '_user_id' not in session


def test_user_roles(app):
    """Test the user role functionality."""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        marketer = User.query.filter_by(username='marketer').first()
        analytics = User.query.filter_by(username='analytics').first()
        
        assert admin.is_admin() is True
        assert admin.is_marketer() is True
        assert admin.is_analytics() is True
        
        assert marketer.is_admin() is False
        assert marketer.is_marketer() is True
        assert marketer.is_analytics() is True
        
        assert analytics.is_admin() is False
        assert analytics.is_marketer() is False
        assert analytics.is_analytics() is True


def test_register_user(client, auth):
    """Test user registration (requires admin)."""
    auth.login()
    response = client.post(
        '/auth/register',
        data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'password2': 'newpassword',
            'role': 'marketer'
        }
    )
    assert response.headers.get('Location') == 'http://localhost/auth/users'
    
    with client.application.app_context():
        assert User.query.filter_by(username='newuser').first() is not None


def test_admin_access_required(client, auth):
    """Test that admin-only routes are protected."""
    # Login as non-admin
    auth.login(username='marketer', password='password')
    
    # Try to access user management
    response = client.get('/auth/users')
    assert response.status_code == 302  # Redirect to login page
    
    # Try to register a new user
    response = client.get('/auth/register')
    assert response.status_code == 302  # Redirect to login page


def test_change_password(client, auth):
    """Test password change functionality."""
    auth.login()
    
    # Change password
    response = client.post(
        '/auth/change_password',
        data={
            'current_password': 'password',
            'new_password': 'newpassword',
            'confirm_password': 'newpassword'
        },
        follow_redirects=True
    )
    assert b'Your password has been updated' in response.data
    
    # Logout and login with new password
    auth.logout()
    response = client.post(
        '/auth/login',
        data={'username': 'admin', 'password': 'newpassword'}
    )
    assert response.headers.get('Location') == 'http://localhost/content/dashboard'


def test_change_password_wrong_current(client, auth):
    """Test password change with incorrect current password."""
    auth.login()
    
    response = client.post(
        '/auth/change_password',
        data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword',
            'confirm_password': 'newpassword'
        },
        follow_redirects=True
    )
    assert b'Current password is incorrect' in response.data
