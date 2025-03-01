"""
Configuration for pytest fixtures.
"""

import os
import tempfile
import pytest
from app import create_app, db
from app.auth.models import User
from app.content.models import Website, Page, ContentVersion
from app.splitest.models import SplitTest, TestVariant
from app.analytics.models import VisitorSession, Conversion, PageView

@pytest.fixture
def app():
    """
    Create and configure a Flask app for testing.
    """
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with testing config
    app = create_app('testing')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'TESTING': True,
        'SERVER_NAME': 'localhost',
    })
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
        _load_test_data()
    
    # Return the app for testing
    yield app
    
    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """
    A test client for the app.
    """
    return app.test_client()

@pytest.fixture
def runner(app):
    """
    A test CLI runner for the app.
    """
    return app.test_cli_runner()

def _load_test_data():
    """
    Load test data into the database.
    """
    # Create test users
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('password')
    
    marketer = User(username='marketer', email='marketer@example.com', role='marketer')
    marketer.set_password('password')
    
    analytics = User(username='analytics', email='analytics@example.com', role='analytics')
    analytics.set_password('password')
    
    db.session.add_all([admin, marketer, analytics])
    db.session.commit()
    
    # Create test website
    website = Website(
        name='Test Website',
        domain='test.example.com',
        directory='test_website'
    )
    db.session.add(website)
    db.session.commit()
    
    # Create test pages
    home_page = Page(
        website_id=website.id,
        path='/index.html',
        title='Home Page'
    )
    
    about_page = Page(
        website_id=website.id,
        path='/about.html',
        title='About Page'
    )
    
    contact_page = Page(
        website_id=website.id,
        path='/contact.html',
        title='Contact Page'
    )
    
    db.session.add_all([home_page, about_page, contact_page])
    db.session.commit()
    
    # Create test content versions
    home_version = ContentVersion(
        page_id=home_page.id,
        content_hash='abc123',
        content_json='{"#title": "Welcome to our website", "#content": "This is the home page content."}',
        version_type='content',
        created_by=admin.id,
        is_active=True
    )
    
    db.session.add(home_version)
    db.session.commit()
    
    # Create test split test
    split_test = SplitTest(
        page_id=home_page.id,
        name='Homepage Headline Test',
        test_type='content',
        goal_page_id=contact_page.id,
        created_by=marketer.id,
        is_active=True
    )
    db.session.add(split_test)
    db.session.commit()
    
    # Create test variants
    variant_a = TestVariant(
        test_id=split_test.id,
        name='Control',
        content_version_id=home_version.id,
        weight=1
    )
    
    # Create alternative version
    home_version_b = ContentVersion(
        page_id=home_page.id,
        content_hash='def456',
        content_json='{"#title": "Discover our amazing services", "#content": "This is the alternative home page content."}',
        version_type='content',
        created_by=marketer.id,
        is_active=False
    )
    db.session.add(home_version_b)
    db.session.commit()
    
    variant_b = TestVariant(
        test_id=split_test.id,
        name='Variation',
        content_version_id=home_version_b.id,
        weight=1
    )
    
    db.session.add_all([variant_a, variant_b])
    db.session.commit()

@pytest.fixture
def auth(client):
    """Helper class to handle authentication in tests."""
    class AuthActions:
        def login(self, username='admin', password='password'):
            return client.post(
                '/auth/login',
                data={'username': username, 'password': password}
            )
            
        def logout(self):
            return client.get('/auth/logout')
    
    return AuthActions()
