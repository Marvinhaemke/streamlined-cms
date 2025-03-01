"""
Tests for analytics functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from app.analytics.models import PageView, VisitorSession, Conversion
from app.analytics.utils import (record_page_view, anonymize_ip, get_page_views_by_date,
                                get_test_results, get_website_stats)


def test_record_page_view(app):
    """Test recording a page view."""
    with app.app_context():
        page_view = record_page_view(
            page_id=1,
            visitor_id="test_visitor",
            user_agent="Test User Agent",
            ip_address="192.168.1.1",
            referrer="https://example.com/ref"
        )
        
        assert page_view is not None
        assert page_view.page_id == 1
        assert page_view.visitor_id == "test_visitor"
        assert page_view.user_agent == "Test User Agent"
        assert page_view.ip_address == "192.168.0.0"  # Anonymized
        assert page_view.referrer == "https://example.com/ref"


def test_anonymize_ip():
    """Test IP address anonymization."""
    # IPv4
    ip = "192.168.1.1"
    anon_ip = anonymize_ip(ip)
    assert anon_ip == "192.168.0.0"
    
    # IPv6
    ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    anon_ip = anonymize_ip(ip)
    assert anon_ip.startswith("2001:0db8:85a3:0000:0000:0000:0000:0000")
    
    # None
    assert anonymize_ip(None) is None


def test_get_page_views_by_date(app):
    """Test getting page views grouped by date."""
    with app.app_context():
        from app import db
        
        # Add some test page views with specific dates
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        
        # Add views for today
        for i in range(5):
            view = PageView(
                page_id=1,
                visitor_id=f"today_visitor_{i}",
                created_at=datetime.utcnow()
            )
            db.session.add(view)
        
        # Add views for yesterday
        for i in range(3):
            view = PageView(
                page_id=1,
                visitor_id=f"yesterday_visitor_{i}",
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(view)
        
        # Add views for two days ago
        for i in range(2):
            view = PageView(
                page_id=1,
                visitor_id=f"two_days_ago_visitor_{i}",
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            db.session.add(view)
        
        db.session.commit()
        
        # Get views by date
        views = get_page_views_by_date(1, days=3)
        
        assert len(views) >= 3
        assert views[today] == 5
        assert views[yesterday] == 3
        assert views[two_days_ago] == 2


def test_get_test_results(app):
    """Test getting test results."""
    with app.app_context():
        from app import db
        
        # Get test
        from app.splitest.models import SplitTest
        test = SplitTest.query.get(1)
        
        # Add some visitor sessions and conversions
        variants = test.variants.all()
        
        # Variant A: 50 visitors, 10 conversions (20%)
        for i in range(50):
            session = VisitorSession(
                split_test_id=test.id,
                variant_id=variants[0].id,
                visitor_id=f"results_visitor_a_{i}"
            )
            db.session.add(session)
            
            if i < 10:
                conversion = Conversion(
                    split_test_id=test.id,
                    variant_id=variants[0].id,
                    visitor_id=f"results_visitor_a_{i}"
                )
                db.session.add(conversion)
        
        # Variant B: 40 visitors, 12 conversions (30%)
        for i in range(40):
            session = VisitorSession(
                split_test_id=test.id,
                variant_id=variants[1].id,
                visitor_id=f"results_visitor_b_{i}"
            )
            db.session.add(session)
            
            if i < 12:
                conversion = Conversion(
                    split_test_id=test.id,
                    variant_id=variants[1].id,
                    visitor_id=f"results_visitor_b_{i}"
                )
                db.session.add(conversion)
        
        db.session.commit()
        
        # Get results
        results = get_test_results(test.id)
        
        assert results is not None
        assert 'test' in results
        assert 'results' in results
        assert 'total_visitors' in results
        assert 'total_conversions' in results
        assert 'avg_conversion_rate' in results
        
        assert results['total_visitors'] == 90
        assert results['total_conversions'] == 22
        assert results['avg_conversion_rate'] == 22 / 90 * 100
        
        # Check variant results
        assert len(results['results']) == 2
        
        variant_a = next(r for r in results['results'] if r['name'] == 'Control')
        variant_b = next(r for r in results['results'] if r['name'] == 'Variation')
        
        assert variant_a['visitors'] == 50
        assert variant_a['conversions'] == 10
        assert variant_a['conversion_rate'] == 20.0
        
        assert variant_b['visitors'] == 40
        assert variant_b['conversions'] == 12
        assert variant_b['conversion_rate'] == 30.0
        assert variant_b['relative_improvement'] == 50.0  # 30% is 50% better than 20%


def test_get_website_stats(app):
    """Test getting overall website statistics."""
    with app.app_context():
        from app import db
        
        # Add some page views for different pages
        website_id = 1
        
        # Add views for each page
        page_ids = [1, 2, 3]  # Home, About, Contact
        
        for page_id in page_ids:
            for i in range(page_id * 10):  # Different number for each page
                view = PageView(
                    page_id=page_id,
                    visitor_id=f"stats_visitor_{page_id}_{i % 5}",  # Some duplicates
                    created_at=datetime.utcnow() - timedelta(days=i % 3)
                )
                db.session.add(view)
        
        db.session.commit()
        
        # Get website stats
        stats = get_website_stats(website_id, days=7)
        
        assert stats is not None
        assert 'total_views' in stats
        assert 'unique_visitors' in stats
        assert 'views_by_page' in stats
        assert 'views_by_date' in stats
        
        assert stats['total_views'] == 10 + 20 + 30  # Sum of all page views
        assert stats['unique_visitors'] <= stats['total_views']  # Should be fewer unique visitors
        
        # Check views by page
        assert len(stats['views_by_page']) == 3
        assert stats['views_by_page'].get('1') == 10
        assert stats['views_by_page'].get('2') == 20
        assert stats['views_by_page'].get('3') == 30
        
        # Check views by date
        assert len(stats['views_by_date']) == 7  # 7 days


def test_analytics_dashboard(client, auth):
    """Test analytics dashboard page."""
    auth.login()
    response = client.get('/analytics/dashboard')
    
    assert response.status_code == 200
    assert b'Analytics Dashboard' in response.data


def test_website_stats_page(client, auth):
    """Test website stats page."""
    auth.login()
    response = client.get('/analytics/website/1')
    
    assert response.status_code == 200
    assert b'Analytics for Test Website' in response.data


def test_page_stats_page(client, auth):
    """Test page stats page."""
    auth.login()
    response = client.get('/analytics/page/1')
    
    assert response.status_code == 200
    assert b'Analytics for Home Page' in response.data


def test_test_stats_page(client, auth):
    """Test test stats page."""
    auth.login()
    response = client.get('/analytics/test/1')
    
    assert response.status_code == 200
    assert b'Results for Homepage Headline Test' in response.data


def test_api_record_view(client):
    """Test API endpoint to record a page view."""
    response = client.post(
        '/api/page_view',
        json={'page_id': 1}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_export_test_data(client, auth):
    """Test exporting test data as CSV."""
    auth.login()
    response = client.get('/analytics/export/test/1')
    
    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'text/csv'
    assert 'attachment; filename=test_1_results.csv' in response.headers.get('Content-disposition')
    
    # Check CSV content
    csv_data = response.data.decode('utf-8')
    assert 'Variant,Visitors,Conversions,Conversion Rate' in csv_data
    assert 'Control' in csv_data
    assert 'Variation' in csv_data
    assert 'TOTAL' in csv_data


def test_access_control(client, auth):
    """Test that analytics pages require authentication."""
    # Without login
    response = client.get('/analytics/dashboard')
    assert response.status_code == 302  # Redirect to login
    
    # With login
    auth.login()
    response = client.get('/analytics/dashboard')
    assert response.status_code == 200
    
    # Check role-based access
    auth.logout()
    auth.login(username='analytics', password='password')
    
    # Analytics role should be able to view analytics
    response = client.get('/analytics/dashboard')
    assert response.status_code == 200
    
    # But not create split tests (requires marketer role)
    response = client.get('/splitest/test/new/1')
    assert response.status_code == 302  # Redirect to login
