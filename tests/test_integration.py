"""
Integration tests for the Streamlined CMS.
"""

import pytest
import json
import os
from app import create_app, db
from app.auth.models import User
from app.content.models import Website, Page, ContentVersion
from app.splitest.models import SplitTest, TestVariant
from app.analytics.models import VisitorSession, Conversion, PageView


def test_end_to_end_flow(client, auth):
    """Test the complete user flow from login to content editing to split testing."""
    # 1. Admin logs in
    auth.login()
    
    # 2. Create a new website
    response = client.post(
        '/website/new',
        data={
            'name': 'Integration Test Site',
            'domain': 'integration.example.com'
        },
        follow_redirects=True
    )
    assert b'Website Integration Test Site created successfully' in response.data
    
    # Get the website ID
    with client.application.app_context():
        website = Website.query.filter_by(domain='integration.example.com').first()
        website_id = website.id
    
    # 3. Create a new page
    response = client.post(
        f'/page/new/{website_id}',
        data={
            'title': 'Test Landing Page',
            'path': '/landing.html'
        },
        follow_redirects=True
    )
    assert b'Page Test Landing Page created successfully' in response.data
    
    # Get the page ID
    with client.application.app_context():
        page = Page.query.filter_by(website_id=website_id, path='/landing.html').first()
        page_id = page.id
    
    # 4. Save content version
    content = {
        '#headline': 'Welcome to our site',
        '#cta': 'Sign up now'
    }
    
    response = client.post(
        f'/api/page/{page_id}/content',
        json={'content': content}
    )
    data = json.loads(response.data)
    assert data['success'] is True
    
    # 5. Create a goal page
    response = client.post(
        f'/page/new/{website_id}',
        data={
            'title': 'Thank You Page',
            'path': '/thank-you.html'
        },
        follow_redirects=True
    )
    assert b'Page Thank You Page created successfully' in response.data
    
    # Get the goal page ID
    with client.application.app_context():
        goal_page = Page.query.filter_by(website_id=website_id, path='/thank-you.html').first()
        goal_page_id = goal_page.id
    
    # 6. Create a split test
    response = client.post(
        f'/splitest/test/new/{page_id}',
        data={
            'name': 'Landing Page Headline Test',
            'test_type': 'content',
            'goal_page_id': goal_page_id
        },
        follow_redirects=True
    )
    assert b'Split test created successfully' in response.data
    
    # Get the test ID
    with client.application.app_context():
        test = SplitTest.query.filter_by(page_id=page_id).first()
        test_id = test.id
    
    # 7. Create another content version (variant B)
    content_b = {
        '#headline': 'Discover our amazing services',
        '#cta': 'Get started today'
    }
    
    response = client.post(
        f'/api/page/{page_id}/content',
        json={'content': content_b}
    )
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Get the content version IDs
    with client.application.app_context():
        version_a = ContentVersion.query.filter_by(
            page_id=page_id, 
            is_active=True
        ).first()
        
        version_b = ContentVersion.query.filter_by(
            page_id=page_id, 
            is_active=False
        ).first()
        
        assert version_a is not None
        assert version_b is not None
    
    # 8. Add variants to the test
    response = client.post(
        f'/splitest/test/{test_id}/variant/add',
        data={
            'name': 'Control',
            'content_version_id': version_a.id,
            'weight': 1
        },
        follow_redirects=True
    )
    assert b'Variant added successfully' in response.data
    
    response = client.post(
        f'/splitest/test/{test_id}/variant/add',
        data={
            'name': 'Variation B',
            'content_version_id': version_b.id,
            'weight': 1
        },
        follow_redirects=True
    )
    assert b'Variant added successfully' in response.data
    
    # 9. Start the test
    response = client.post(
        f'/splitest/test/{test_id}/start',
        follow_redirects=True
    )
    assert b'Test started successfully' in response.data
    
    # 10. Simulate visitor sessions and conversions
    with client.application.app_context():
        variants = TestVariant.query.filter_by(test_id=test_id).all()
        
        # Add 10 visitor sessions and 2 conversions for variant A
        for i in range(10):
            session = VisitorSession(
                split_test_id=test_id,
                variant_id=variants[0].id,
                visitor_id=f"flow_visitor_a_{i}"
            )
            db.session.add(session)
            
            # Add page view
            view = PageView(
                page_id=page_id,
                visitor_id=f"flow_visitor_a_{i}"
            )
            db.session.add(view)
            
            # 20% conversion rate
            if i < 2:
                conversion = Conversion(
                    split_test_id=test_id,
                    variant_id=variants[0].id,
                    visitor_id=f"flow_visitor_a_{i}"
                )
                db.session.add(conversion)
                
                # Add page view to goal page
                goal_view = PageView(
                    page_id=goal_page_id,
                    visitor_id=f"flow_visitor_a_{i}"
                )
                db.session.add(goal_view)
        
        # Add 10 visitor sessions and 3 conversions for variant B
        for i in range(10):
            session = VisitorSession(
                split_test_id=test_id,
                variant_id=variants[1].id,
                visitor_id=f"flow_visitor_b_{i}"
            )
            db.session.add(session)
            
            # Add page view
            view = PageView(
                page_id=page_id,
                visitor_id=f"flow_visitor_b_{i}"
            )
            db.session.add(view)
            
            # 30% conversion rate
            if i < 3:
                conversion = Conversion(
                    split_test_id=test_id,
                    variant_id=variants[1].id,
                    visitor_id=f"flow_visitor_b_{i}"
                )
                db.session.add(conversion)
                
                # Add page view to goal page
                goal_view = PageView(
                    page_id=goal_page_id,
                    visitor_id=f"flow_visitor_b_{i}"
                )
                db.session.add(goal_view)
        
        db.session.commit()
    
    # 11. Check test results
    response = client.get(f'/analytics/test/{test_id}')
    assert response.status_code == 200
    assert b'Results for Landing Page Headline Test' in response.data
    assert b'20.0%' in response.data  # Control conversion rate
    assert b'30.0%' in response.data  # Variation B conversion rate
    
    # 12. Stop the test
    response = client.post(
        f'/splitest/test/{test_id}/stop',
        follow_redirects=True
    )
    assert b'Test stopped successfully' in response.data
    
    # 13. Check that test is marked as inactive
    with client.application.app_context():
        test = SplitTest.query.get(test_id)
        assert test.is_active is False
        assert test.end_date is not None


def test_different_user_roles(client, auth):
    """Test that different user roles have appropriate permissions."""
    # 1. Admin can access everything
    auth.login(username='admin', password='password')
    
    response = client.get('/content/dashboard')
    assert response.status_code == 200
    
    response = client.get('/splitest/tests')
    assert response.status_code == 200
    
    response = client.get('/analytics/dashboard')
    assert response.status_code == 200
    
    response = client.get('/auth/users')
    assert response.status_code == 200
    
    auth.logout()
    
    # 2. Marketer can access content, split tests, and analytics
    auth.login(username='marketer', password='password')
    
    response = client.get('/content/dashboard')
    assert response.status_code == 200
    
    response = client.get('/splitest/tests')
    assert response.status_code == 200
    
    response = client.get('/analytics/dashboard')
    assert response.status_code == 200
    
    # But not user management
    response = client.get('/auth/users')
    assert response.status_code == 302  # Redirect to login
    
    auth.logout()
    
    # 3. Analytics user can only access analytics
    auth.login(username='analytics', password='password')
    
    # Can access analytics
    response = client.get('/analytics/dashboard')
    assert response.status_code == 200
    
    # But not content management
    response = client.post(
        '/website/new',
        data={
            'name': 'Test Site',
            'domain': 'test.com'
        }
    )
    assert response.status_code == 302  # Redirect to login
    
    # Or split testing
    response = client.get('/splitest/tests')
    assert response.status_code == 200  # Can view tests
    
    # But can't create tests
    with client.application.app_context():
        page = Page.query.first()
        page_id = page.id
    
    response = client.get(f'/splitest/test/new/{page_id}')
    assert response.status_code == 302  # Redirect to login
