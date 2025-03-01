from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.analytics import bp
from app.analytics.models import PageView, VisitorSession, Conversion
from app.content.models import Website, Page
from app.splitest.models import SplitTest
from app.auth.routes import admin_required, marketer_required
from app.analytics.utils import (record_page_view, get_page_views_by_date,
                                get_test_results, get_website_stats)
from app.utils import get_visitor_id  # Import from common utils instead
from datetime import datetime, timedelta

@bp.route('/dashboard')
@login_required
def dashboard():
    """Analytics dashboard showing recent stats."""
    # Get all websites
    websites = Website.query.all()
    
    # Get recent test results
    recent_tests = SplitTest.query.order_by(SplitTest.created_at.desc()).limit(5).all()
    
    return render_template('analytics/dashboard.html', title='Analytics Dashboard',
                          websites=websites, recent_tests=recent_tests)

@bp.route('/website/<int:website_id>')
@login_required
def website_stats(website_id):
    """Analytics for a specific website."""
    website = Website.query.get_or_404(website_id)
    
    # Get time range
    days = request.args.get('days', 30, type=int)
    
    # Get website statistics
    stats = get_website_stats(website.id, days)
    
    # Get pages for this website
    pages = Page.query.filter_by(website_id=website.id).all()
    
    return render_template('analytics/website_stats.html', title=f'Analytics for {website.name}',
                          website=website, stats=stats, pages=pages, days=days)

@bp.route('/page/<int:page_id>')
@login_required
def page_stats(page_id):
    """Analytics for a specific page."""
    page = Page.query.get_or_404(page_id)
    
    # Get time range
    days = request.args.get('days', 30, type=int)
    
    # Get page views by date
    views_by_date = get_page_views_by_date(page.id, days)
    
    # Get total views and unique visitors
    start_date = datetime.utcnow() - timedelta(days=days)
    views = PageView.query.filter(
        PageView.page_id == page.id,
        PageView.created_at >= start_date
    ).all()
    
    total_views = len(views)
    unique_visitors = len(set(view.visitor_id for view in views))
    
    # Get referring URLs
    referrers = {}
    for view in views:
        if view.referrer:
            referrers[view.referrer] = referrers.get(view.referrer, 0) + 1
    
    # Get active tests for this page
    active_tests = SplitTest.query.filter_by(page_id=page.id, is_active=True).all()
    
    return render_template('analytics/page_stats.html', title=f'Analytics for {page.title}',
                          page=page, views_by_date=views_by_date, total_views=total_views,
                          unique_visitors=unique_visitors, referrers=referrers,
                          active_tests=active_tests, days=days)

@bp.route('/test/<int:test_id>')
@login_required
def test_stats(test_id):
    """Detailed statistics for a split test."""
    test_results = get_test_results(test_id)
    
    if not test_results:
        flash('Test not found', 'danger')
        return redirect(url_for('analytics.dashboard'))
    
    return render_template('analytics/test_stats.html', title=f'Results for {test_results["test"].name}',
                          test=test_results["test"], results=test_results["results"],
                          total_visitors=test_results["total_visitors"],
                          total_conversions=test_results["total_conversions"],
                          avg_conversion_rate=test_results["avg_conversion_rate"])

@bp.route('/api/page_view', methods=['POST'])
def record_view():
    """API endpoint to record a page view."""
    page_id = request.json.get('page_id')
    
    if not page_id:
        return jsonify({'error': 'Page ID is required'}), 400
    
    # Get visitor ID from cookie
    visitor_id = get_visitor_id(request)
    
    # Get additional information
    user_agent = request.headers.get('User-Agent')
    ip_address = request.remote_addr
    referrer = request.referrer
    
    # Record page view
    page_view = record_page_view(page_id, visitor_id, user_agent, ip_address, referrer)
    
    return jsonify({'success': True})

@bp.route('/export/test/<int:test_id>')
@login_required
def export_test_data(test_id):
    """Export test data as CSV."""
    test = SplitTest.query.get_or_404(test_id)
    
    # Build CSV data
    csv_data = [
        ['Variant', 'Visitors', 'Conversions', 'Conversion Rate']
    ]
    
    for variant in test.variants:
        visitors = variant.visitor_sessions.count()
        conversions = variant.conversions.count()
        
        conversion_rate = 0
        if visitors > 0:
            conversion_rate = (conversions / visitors) * 100
        
        csv_data.append([
            variant.name,
            visitors,
            conversions,
            f'{conversion_rate:.2f}%'
        ])
    
    # Add totals
    total_visitors = sum(v.visitor_sessions.count() for v in test.variants)
    total_conversions = sum(v.conversions.count() for v in test.variants)
    avg_rate = 0
    if total_visitors > 0:
        avg_rate = (total_conversions / total_visitors) * 100
    
    csv_data.append(['TOTAL', total_visitors, total_conversions, f'{avg_rate:.2f}%'])
    
    # Generate CSV response
    from io import StringIO
    import csv
    
    si = StringIO()
    writer = csv.writer(si)
    writer.writerows(csv_data)
    
    from flask import Response
    output = si.getvalue()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=test_{test.id}_results.csv"}
    )