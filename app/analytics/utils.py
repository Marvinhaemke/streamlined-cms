from app import db
from app.analytics.models import PageView, VisitorSession, Conversion
from app.content.models import Page, Website
from app.splitest.models import SplitTest, TestVariant
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

def record_page_view(page_id, visitor_id, user_agent=None, ip_address=None, referrer=None):
    """
    Record a page view.
    
    Args:
        page_id (int): ID of the page
        visitor_id (str): Visitor ID
        user_agent (str, optional): Browser user agent
        ip_address (str, optional): Visitor IP address
        referrer (str, optional): Referrer URL
        
    Returns:
        PageView: Created PageView instance
    """
    page_view = PageView(
        page_id=page_id,
        visitor_id=visitor_id,
        user_agent=user_agent,
        ip_address=anonymize_ip(ip_address) if ip_address else None,
        referrer=referrer
    )
    
    db.session.add(page_view)
    db.session.commit()
    
    return page_view

def anonymize_ip(ip_address):
    """
    Anonymize an IP address.
    
    Args:
        ip_address (str): IP address to anonymize
        
    Returns:
        str: Anonymized IP address
    """
    if not ip_address:
        return None
    
    # Handle IPv4
    if '.' in ip_address:
        parts = ip_address.split('.')
        return f"{parts[0]}.{parts[1]}.0.0"
    
    # Handle IPv6
    if ':' in ip_address:
        parts = ip_address.split(':')
        return f"{parts[0]}:{parts[1]}:{parts[2]}:0000:0000:0000:0000:0000"
    
    return None

def get_page_views_by_date(page_id, days=30):
    """
    Get page views grouped by date.
    
    Args:
        page_id (int): ID of the page
        days (int, optional): Number of days to include
        
    Returns:
        dict: Dictionary with dates and view counts
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    views = PageView.query.filter(
        PageView.page_id == page_id,
        PageView.created_at >= start_date
    ).all()
    
    # Group by date
    view_dates = [view.created_at.date() for view in views]
    
    # Count views per date
    view_counts = defaultdict(int)
    for date in view_dates:
        view_counts[date] += 1
    
    # Fill in missing dates
    result = {}
    current_date = start_date.date()
    end_date = datetime.utcnow().date()
    
    while current_date <= end_date:
        result[current_date] = view_counts.get(current_date, 0)
        current_date += timedelta(days=1)
    
    return result

def get_test_results(test_id):
    """
    Get detailed results for a split test.
    
    Args:
        test_id (int): ID of the split test
        
    Returns:
        dict: Dictionary with test results
    """
    test = SplitTest.query.get(test_id)
    
    if not test:
        return None
    
    variants = test.variants.all()
    results = []
    
    for variant in variants:
        # Get visitor sessions
        sessions = VisitorSession.query.filter_by(
            split_test_id=test.id,
            variant_id=variant.id
        ).all()
        
        # Get conversions
        conversions = Conversion.query.filter_by(
            split_test_id=test.id,
            variant_id=variant.id
        ).all()
        
        # Calculate metrics
        visitors = len(sessions)
        conversion_count = len(conversions)
        conversion_rate = 0
        
        if visitors > 0:
            conversion_rate = (conversion_count / visitors) * 100
        
        # Calculate confidence interval if we have sufficient data
        if visitors > 10 and conversion_count > 0:
            # Wilson score interval
            z = 1.96  # 95% confidence
            p = conversion_rate / 100
            
            denominator = 1 + z**2/visitors
            centre_adjusted_probability = p + z*z/(2*visitors)
            adjusted_standard_deviation = np.sqrt((p*(1-p) + z*z/(4*visitors))/visitors)
            
            lower_bound = (centre_adjusted_probability - z*adjusted_standard_deviation) / denominator * 100
            upper_bound = (centre_adjusted_probability + z*adjusted_standard_deviation) / denominator * 100
        else:
            lower_bound = 0
            upper_bound = 0
        
        results.append({
            'variant_id': variant.id,
            'name': variant.name,
            'visitors': visitors,
            'conversions': conversion_count,
            'conversion_rate': conversion_rate,
            'confidence_interval': [lower_bound, upper_bound]
        })
    
    # Calculate relative improvement
    if len(results) > 1 and results[0]['visitors'] > 0:
        baseline_rate = results[0]['conversion_rate']
        
        for i in range(1, len(results)):
            if baseline_rate > 0:
                relative_improvement = ((results[i]['conversion_rate'] - baseline_rate) / baseline_rate) * 100
            else:
                relative_improvement = 0
            
            results[i]['relative_improvement'] = relative_improvement
    
    total_visitors = sum(r['visitors'] for r in results)
    total_conversions = sum(r['conversions'] for r in results)
    avg_conversion_rate = 0
    
    if total_visitors > 0:
        avg_conversion_rate = (total_conversions / total_visitors) * 100
    
    return {
        'test': test,
        'results': results,
        'total_visitors': total_visitors,
        'total_conversions': total_conversions,
        'avg_conversion_rate': avg_conversion_rate
    }

def get_website_stats(website_id, days=30):
    """
    Get overall statistics for a website.
    
    Args:
        website_id (int): ID of the website
        days (int, optional): Number of days to include
        
    Returns:
        dict: Dictionary with website statistics
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all pages for this website
    pages = Page.query.filter_by(website_id=website_id).all()
    page_ids = [page.id for page in pages]
    
    if not page_ids:
        return {
            'total_views': 0,
            'unique_visitors': 0,
            'views_by_page': {},
            'views_by_date': {}
        }
    
    # Get page views
    views = PageView.query.filter(
        PageView.page_id.in_(page_ids),
        PageView.created_at >= start_date
    ).all()
    
    # Calculate metrics
    total_views = len(views)
    unique_visitors = len(set(view.visitor_id for view in views))
    
    # Group views by page
    views_by_page = defaultdict(int)
    for view in views:
        views_by_page[view.page_id] += 1
    
    # Group views by date
    view_dates = [view.created_at.date() for view in views]
    views_by_date = defaultdict(int)
    for date in view_dates:
        views_by_date[date] += 1
    
    # Fill in missing dates
    date_results = {}
    current_date = start_date.date()
    end_date = datetime.utcnow().date()
    
    while current_date <= end_date:
        date_results[current_date.strftime('%Y-%m-%d')] = views_by_date.get(current_date, 0)
        current_date += timedelta(days=1)
    
    return {
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'views_by_page': dict(views_by_page),
        'views_by_date': date_results
    }
