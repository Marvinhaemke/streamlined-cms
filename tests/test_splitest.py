"""
Tests for split testing functionality.
"""

import pytest
import json
from app.splitest.models import SplitTest, TestVariant
from app.analytics.models import VisitorSession, Conversion
from app.splitest.utils import (create_split_test, add_variant, get_visitor_id,
                               assign_variant, calculate_statistical_significance)


def test_test_list(client, auth):
    """Test split test list page."""
    auth.login()
    response = client.get('/splitest/tests')
    
    assert response.status_code == 200
    assert b'Split Tests' in response.data
    assert b'Homepage Headline Test' in response.data


def test_test_detail(client, auth):
    """Test split test detail page."""
    auth.login()
    response = client.get('/splitest/test/1')
    
    assert response.status_code == 200
    assert b'Homepage Headline Test' in response.data
    assert b'Control' in response.data
    assert b'Variation' in response.data


def test_create_test(client, auth):
    """Test creation of a new split test."""
    auth.login()
    
    # First, create the test
    response = client.post(
        '/splitest/test/new/2',  # Create test for About page
        data={
            'name': 'About Page Test',
            'test_type': 'content',
            'goal_page_id': '3'  # Contact page is goal
        },
        follow_redirects=True
    )
    
    assert b'Split test created successfully' in response.data
    
    with client.application.app_context():
        test = SplitTest.query.filter_by(name='About Page Test').first()
        assert test is not None
        assert test.page_id == 2
        assert test.goal_page_id == 3
        assert test.test_type == 'content'


def test_add_variant(client, auth):
    """Test adding a variant to a split test."""
    auth.login()
    
    # Create a content version to use
    with client.application.app_context():
        from app import db
        from app.content.models import ContentVersion
        
        content_version = ContentVersion(
            page_id=2,  # About page
            content_hash='test123',
            content_json='{"#title": "About Us Variant"}',
            version_type='content',
            created_by=1,  # Admin user
            is_active=False
        )
        
        db.session.add(content_version)
        db.session.commit()
        
        version_id = content_version.id
    
    # First create a test
    response = client.post(
        '/splitest/test/new/2',  # Create test for About page
        data={
            'name': 'About Page Test 2',
            'test_type': 'content',
            'goal_page_id': '3'  # Contact page is goal
        },
        follow_redirects=True
    )
    
    with client.application.app_context():
        test = SplitTest.query.filter_by(name='About Page Test 2').first()
        test_id = test.id
    
    # Now add a variant
    response = client.post(
        f'/splitest/test/{test_id}/variant/add',
        data={
            'name': 'Test Variant',
            'content_version_id': version_id,
            'weight': 1
        },
        follow_redirects=True
    )
    
    assert b'Variant added successfully' in response.data
    
    with client.application.app_context():
        variant = TestVariant.query.filter_by(test_id=test_id).first()
        assert variant is not None
        assert variant.name == 'Test Variant'
        assert variant.content_version_id == version_id


def test_start_stop_test(client, auth):
    """Test starting and stopping a split test."""
    auth.login()
    
    # Create test with two variants
    with client.application.app_context():
        from app import db
        from app.content.models import ContentVersion
        
        # Create two content versions
        version1 = ContentVersion(
            page_id=2,  # About page
            content_hash='version1',
            content_json='{"#title": "About Us Version 1"}',
            version_type='content',
            created_by=1,
            is_active=False
        )
        
        version2 = ContentVersion(
            page_id=2,  # About page
            content_hash='version2',
            content_json='{"#title": "About Us Version 2"}',
            version_type='content',
            created_by=1,
            is_active=False
        )
        
        db.session.add_all([version1, version2])
        db.session.commit()
        
        # Create test
        test = create_split_test(
            page_id=2,
            name='Start/Stop Test',
            test_type='content',
            goal_page_id=3,
            user_id=1
        )
        
        # Add variants
        add_variant(test.id, 'Control', version1.id, 1)
        add_variant(test.id, 'Variant B', version2.id, 1)
        
        # Set as inactive initially
        test.is_active = False
        db.session.commit()
        
        test_id = test.id
    
    # Start the test
    response = client.post(
        f'/splitest/test/{test_id}/start',
        follow_redirects=True
    )
    
    assert b'Test started successfully' in response.data
    
    with client.application.app_context():
        test = SplitTest.query.get(test_id)
        assert test.is_active is True
    
    # Stop the test
    response = client.post(
        f'/splitest/test/{test_id}/stop',
        follow_redirects=True
    )
    
    assert b'Test stopped successfully' in response.data
    
    with client.application.app_context():
        test = SplitTest.query.get(test_id)
        assert test.is_active is False
        assert test.end_date is not None


def test_get_visitor_id():
    """Test getting a visitor ID from a request."""
    from flask import Request
    from werkzeug.test import EnvironBuilder
    
    # Create a test request with no cookie
    builder = EnvironBuilder()
    env = builder.get_environ()
    request = Request(env)
    
    # First call should generate a new ID
    visitor_id = get_visitor_id(request)
    assert visitor_id is not None
    assert len(visitor_id) > 0
    
    # Create a request with an existing visitor cookie
    builder = EnvironBuilder(headers={
        'Cookie': f'visitor_id={visitor_id}'
    })
    env = builder.get_environ()
    request = Request(env)
    
    # Second call should return the same ID
    second_id = get_visitor_id(request)
    assert second_id == visitor_id


def test_assign_variant(app):
    """Test variant assignment for a visitor."""
    with app.app_context():
        # Get an existing test with variants
        test = SplitTest.query.get(1)
        assert test is not None
        
        # Assign visitor to test
        visitor_id = "test_visitor_1"
        variant = assign_variant(test.id, visitor_id)
        
        # Check that assignment was recorded
        session = VisitorSession.query.filter_by(
            split_test_id=test.id,
            visitor_id=visitor_id
        ).first()
        
        assert session is not None
        assert session.variant_id == variant.id
        
        # Ensure consistent assignment
        variant2 = assign_variant(test.id, visitor_id)
        assert variant2.id == variant.id


def test_record_conversion(app):
    """Test recording a conversion."""
    with app.app_context():
        from app.splitest.utils import record_conversion
        
        # Get test info
        test = SplitTest.query.get(1)
        variant = TestVariant.query.filter_by(test_id=test.id).first()
        
        # Record a conversion
        visitor_id = "test_conversion_visitor"
        conversion = record_conversion(test.id, variant.id, visitor_id)
        
        assert conversion is not None
        assert conversion.split_test_id == test.id
        assert conversion.variant_id == variant.id
        assert conversion.visitor_id == visitor_id
        
        # Try recording duplicate conversion
        duplicate = record_conversion(test.id, variant.id, visitor_id)
        assert duplicate is None  # Should prevent duplicates


def test_api_get_variant(client):
    """Test API endpoint to get a split test variant."""
    response = client.get('/api/test/variant?page_id=1&test_type=content')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['active_test'] is True
    assert 'test_id' in data
    assert 'variant_id' in data
    assert 'content_version_id' in data


def test_api_record_conversion(client):
    """Test API endpoint to record a conversion."""
    # First create a test visitor session
    with client.application.app_context():
        from app import db
        
        # Get test and variant
        test = SplitTest.query.get(1)
        variant = TestVariant.query.filter_by(test_id=test.id).first()
        
        # Create visitor session
        visitor_id = "api_test_visitor"
        session = VisitorSession(
            split_test_id=test.id,
            variant_id=variant.id,
            visitor_id=visitor_id
        )
        db.session.add(session)
        db.session.commit()
    
    # Set visitor cookie
    client.set_cookie('localhost', 'visitor_id', visitor_id)
    
    # Record conversion
    response = client.post(
        '/api/test/conversion',
        json={
            'test_id': 1,
            'variant_id': variant.id
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Check conversion was recorded
    with client.application.app_context():
        conversion = Conversion.query.filter_by(
            split_test_id=1,
            visitor_id=visitor_id
        ).first()
        
        assert conversion is not None


def test_calculate_statistical_significance(app):
    """Test calculation of statistical significance for test results."""
    with app.app_context():
        from app import db
        
        # Create a test with some data
        test = SplitTest.query.get(1)
        variants = test.variants.all()
        
        # Add some fake visitor sessions and conversions
        for i in range(100):
            # Control variant: 20% conversion
            session1 = VisitorSession(
                split_test_id=test.id,
                variant_id=variants[0].id,
                visitor_id=f"stat_visitor_control_{i}"
            )
            db.session.add(session1)
            
            if i < 20:  # 20% conversion rate
                conversion1 = Conversion(
                    split_test_id=test.id,
                    variant_id=variants[0].id,
                    visitor_id=f"stat_visitor_control_{i}"
                )
                db.session.add(conversion1)
            
            # Test variant: 30% conversion
            session2 = VisitorSession(
                split_test_id=test.id,
                variant_id=variants[1].id,
                visitor_id=f"stat_visitor_test_{i}"
            )
            db.session.add(session2)
            
            if i < 30:  # 30% conversion rate
                conversion2 = Conversion(
                    split_test_id=test.id,
                    variant_id=variants[1].id,
                    visitor_id=f"stat_visitor_test_{i}"
                )
                db.session.add(conversion2)
        
        db.session.commit()
        
        # Calculate significance
        results = calculate_statistical_significance(test.id)
        
        assert results is not None
        assert len(results) == 2
        
        # Check results for control
        assert results[0]['visitors'] == 100
        assert results[0]['conversions'] == 20
        assert results[0]['conversion_rate'] == 20.0
        
        # Check results for test variant
        assert results[1]['visitors'] == 100
        assert results[1]['conversions'] == 30
        assert results[1]['conversion_rate'] == 30.0
        assert 'relative_improvement' in results[1]
        assert results[1]['relative_improvement'] == 50.0  # 30% is 50% better than 20%
