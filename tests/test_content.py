"""
Tests for content management functionality.
"""

import pytest
import json
from app.content.models import Website, Page, ContentVersion
from app.content.utils import parse_html_content, apply_content_changes


def test_dashboard_access(client, auth):
    """Test the content dashboard is accessible after login."""
    # Without login
    response = client.get('/content/dashboard')
    assert response.status_code == 302  # Redirect to login
    
    # With login
    auth.login()
    response = client.get('/content/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_website_detail(client, auth):
    """Test website detail page."""
    auth.login()
    response = client.get('/website/1')
    assert response.status_code == 200
    assert b'Test Website' in response.data
    assert b'Home Page' in response.data
    assert b'About Page' in response.data
    assert b'Contact Page' in response.data


def test_create_website(client, auth):
    """Test website creation."""
    auth.login()
    response = client.post(
        '/website/new',
        data={
            'name': 'New Website',
            'domain': 'new.example.com'
        },
        follow_redirects=True
    )
    assert b'Website New Website created successfully' in response.data
    
    with client.application.app_context():
        website = Website.query.filter_by(domain='new.example.com').first()
        assert website is not None
        assert website.name == 'New Website'


def test_create_page(client, auth):
    """Test page creation."""
    auth.login()
    response = client.post(
        '/page/new/1',
        data={
            'title': 'New Page',
            'path': '/new-page.html'
        },
        follow_redirects=True
    )
    assert b'Page New Page created successfully' in response.data
    
    with client.application.app_context():
        page = Page.query.filter_by(path='/new-page.html').first()
        assert page is not None
        assert page.title == 'New Page'
        assert page.website_id == 1


def test_api_get_page_content(client, auth):
    """Test API endpoint to get page content."""
    auth.login()
    response = client.get('/api/page/1/content')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'content' in data
    assert '#title' in data['content']
    assert data['content']['#title'] == 'Welcome to our website'


def test_api_save_page_content(client, auth):
    """Test API endpoint to save page content."""
    auth.login()
    content_changes = {
        '#title': 'Updated Title',
        '#content': 'Updated content text.'
    }
    
    response = client.post(
        '/api/page/1/content',
        json={'content': content_changes}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    
    with client.application.app_context():
        # Check that a new content version was created
        content_version = ContentVersion.query.filter_by(
            page_id=1,
            is_active=True
        ).first()
        
        assert content_version is not None
        content_data = json.loads(content_version.content_json)
        assert content_data['#title'] == 'Updated Title'
        assert content_data['#content'] == 'Updated content text.'


def test_parse_html_content():
    """Test parsing of HTML content."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1 id="title">Welcome to our site</h1>
            <div id="content">This is the content.</div>
            <p class="editable-text">Editable paragraph</p>
            <div data-editable="footer">Footer text</div>
        </body>
    </html>
    """
    
    content = parse_html_content(html)
    
    assert content['#title'] == 'Welcome to our site'
    assert content['#content'] == 'This is the content.'
    assert content['.editable-text'] == 'Editable paragraph'
    assert content["[data-editable='footer']"] == 'Footer text'


def test_apply_content_changes():
    """Test applying content changes to HTML."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1 id="title">Original Title</h1>
            <div id="content">Original content.</div>
            <p class="editable-text">Original paragraph</p>
        </body>
    </html>
    """
    
    changes = {
        '#title': 'Updated Title',
        '#content': 'Updated content text.',
        '.editable-text': 'Updated paragraph'
    }
    
    modified_html = apply_content_changes(html, changes)
    
    # Check that changes were applied
    assert 'Updated Title' in modified_html
    assert 'Updated content text.' in modified_html
    assert 'Updated paragraph' in modified_html
    
    # Check that original content was replaced
    assert 'Original Title' not in modified_html
    assert 'Original content.' not in modified_html
    assert 'Original paragraph' not in modified_html


def test_page_detail(client, auth):
    """Test page detail view."""
    auth.login()
    response = client.get('/page/1')
    
    assert response.status_code == 200
    assert b'Home Page' in response.data
    assert b'Content Versions' in response.data


def test_edit_page(client, auth):
    """Test edit page view."""
    auth.login()
    response = client.get('/page/1/edit')
    
    assert response.status_code == 200
    assert b'Edit Home Page' in response.data


def test_content_version_activation(client, auth):
    """Test activation of content versions."""
    auth.login()
    
    # Create a new content version
    with client.application.app_context():
        page = Page.query.get(1)
        user = auth.login()
        
        # Create inactive version
        inactive_version = ContentVersion(
            page_id=page.id,
            content_hash='xyz789',
            content_json='{"#title": "Another Test Title", "#content": "Another test content."}',
            version_type='content',
            created_by=1,  # Admin user
            is_active=False
        )
        
        from app import db
        db.session.add(inactive_version)
        db.session.commit()
        
        version_id = inactive_version.id
    
    # Activate the version
    response = client.post(
        f'/page/1/version/{version_id}/activate',
        follow_redirects=True
    )
    
    assert b'Content version activated successfully' in response.data
    
    # Check that it's now active
    with client.application.app_context():
        version = ContentVersion.query.get(version_id)
        assert version.is_active is True
        
        # Check that other versions are inactive
        other_versions = ContentVersion.query.filter(
            ContentVersion.page_id == 1,
            ContentVersion.id != version_id
        ).all()
        
        for v in other_versions:
            assert v.is_active is False
