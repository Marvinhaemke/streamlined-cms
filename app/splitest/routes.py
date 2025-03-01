from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.splitest import bp
from app.splitest.models import SplitTest, TestVariant
from app.content.models import Page, ContentVersion
from app.auth.routes import admin_required, marketer_required
from app.splitest.utils import (create_split_test, add_variant, 
                              assign_variant, record_conversion, calculate_statistical_significance,
                              get_active_test_for_page, get_variant_for_visitor)
from app.utils import get_visitor_id  # Import from common utils
from datetime import datetime

@bp.route('/tests')
@login_required
def test_list():
    """List all split tests."""
    tests = SplitTest.query.order_by(SplitTest.created_at.desc()).all()
    return render_template('splitest/test_list.html', title='Split Tests', tests=tests)

@bp.route('/page/<int:page_id>/tests')
@login_required
def page_tests(page_id):
    """List split tests for a specific page."""
    page = Page.query.get_or_404(page_id)
    tests = SplitTest.query.filter_by(page_id=page_id).order_by(SplitTest.created_at.desc()).all()
    return render_template('splitest/page_tests.html', title=f'Tests for {page.title}', page=page, tests=tests)

@bp.route('/test/new/<int:page_id>', methods=['GET', 'POST'])
@login_required
@marketer_required
def new_test(page_id):
    """Create a new split test."""
    page = Page.query.get_or_404(page_id)
    
    # Get potential goal pages from the same website
    goal_pages = Page.query.filter_by(website_id=page.website_id).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        test_type = request.form.get('test_type')
        goal_page_id = request.form.get('goal_page_id', type=int)
        
        if not name or not test_type or not goal_page_id:
            flash('All fields are required', 'danger')
            return redirect(url_for('splitest.new_test', page_id=page.id))
        
        # Check if test type is valid
        if test_type not in ['design', 'content']:
            flash('Invalid test type', 'danger')
            return redirect(url_for('splitest.new_test', page_id=page.id))
        
        # Verify goal page exists and is in the same website
        goal_page = Page.query.get(goal_page_id)
        if not goal_page or goal_page.website_id != page.website_id:
            flash('Invalid goal page', 'danger')
            return redirect(url_for('splitest.new_test', page_id=page.id))
        
        # Check if an active test of this type already exists
        existing_test = get_active_test_for_page(page.id, test_type)
        if existing_test:
            flash(f'An active {test_type} test already exists for this page', 'danger')
            return redirect(url_for('splitest.test_detail', test_id=existing_test.id))
        
        # Create test
        test = create_split_test(page.id, name, test_type, goal_page_id, current_user.id)
        
        flash('Split test created successfully. Now add some variants.', 'success')
        return redirect(url_for('splitest.add_variant', test_id=test.id))
    
    return render_template('splitest/new_test.html', title='New Split Test', page=page, goal_pages=goal_pages)

@bp.route('/test/<int:test_id>')
@login_required
def test_detail(test_id):
    """Show split test details and results."""
    test = SplitTest.query.get_or_404(test_id)
    variants = test.variants.all()
    
    # Calculate statistical results
    stats = calculate_statistical_significance(test.id)
    
    return render_template('splitest/test_detail.html', title=test.name, test=test, 
                          variants=variants, stats=stats)

# Change this route to match the endpoint used in the test
@bp.route('/test/<int:test_id>/variant/add', methods=['GET', 'POST'])
@login_required
@marketer_required
def add_variant(test_id):
    """Add a variant to a split test."""
    test = SplitTest.query.get_or_404(test_id)
    page = Page.query.get(test.page_id)
    
    # Get available content versions
    if test.test_type == 'content':
        versions = ContentVersion.query.filter_by(page_id=page.id, version_type='content').all()
    else:  # design test
        versions = ContentVersion.query.filter_by(page_id=page.id, version_type='design').all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        content_version_id = request.form.get('content_version_id', type=int)
        weight = request.form.get('weight', type=int, default=1)
        
        if not name or not content_version_id:
            flash('Name and content version are required', 'danger')
            return redirect(url_for('splitest.add_variant', test_id=test.id))
        
        # Verify content version exists and is correct type
        content_version = ContentVersion.query.get(content_version_id)
        if not content_version or content_version.page_id != page.id or content_version.version_type != test.test_type:
            flash('Invalid content version', 'danger')
            return redirect(url_for('splitest.add_variant', test_id=test.id))
        
        # Add variant
        variant = add_variant(test.id, name, content_version_id, weight)
        
        flash('Variant added successfully', 'success')
        return redirect(url_for('splitest.test_detail', test_id=test.id))
    
    return render_template('splitest/add_variant.html', title='Add Variant', test=test, 
                          page=page, versions=versions)

# Keep this route for backward compatibility
@bp.route('/test/<int:test_id>/variant/add', methods=['GET', 'POST'])
@login_required
@marketer_required
def add_variant_route(test_id):
    """Redirect to the standard add_variant route for backward compatibility."""
    return redirect(url_for('splitest.add_variant', test_id=test_id))

@bp.route('/test/<int:test_id>/start', methods=['POST'])
@login_required
@marketer_required
def start_test(test_id):
    """Start a split test."""
    test = SplitTest.query.get_or_404(test_id)
    
    # Check if test has at least 2 variants
    if test.variants.count() < 2:
        flash('A test needs at least 2 variants', 'danger')
        return redirect(url_for('splitest.test_detail', test_id=test.id))
    
    # Set test as active
    test.is_active = True
    test.start_date = datetime.utcnow()
    test.end_date = None
    db.session.commit()
    
    flash('Test started successfully', 'success')
    return redirect(url_for('splitest.test_detail', test_id=test.id))

@bp.route('/test/<int:test_id>/stop', methods=['POST'])
@login_required
@marketer_required
def stop_test(test_id):
    """Stop a split test."""
    test = SplitTest.query.get_or_404(test_id)
    
    # Set test as inactive
    test.is_active = False
    test.end_date = datetime.utcnow()
    db.session.commit()
    
    flash('Test stopped successfully', 'success')
    return redirect(url_for('splitest.test_detail', test_id=test.id))

@bp.route('/test/<int:test_id>/delete', methods=['POST'])
@login_required
@marketer_required
def delete_test(test_id):
    """Delete a split test."""
    test = SplitTest.query.get_or_404(test_id)
    
    # Delete test
    db.session.delete(test)
    db.session.commit()
    
    flash('Test deleted successfully', 'success')
    return redirect(url_for('splitest.test_list'))

@bp.route('/api/test/variant', methods=['GET'])
def get_test_variant():
    """API endpoint to get a variant for a visitor."""
    page_id = request.args.get('page_id', type=int)
    test_type = request.args.get('test_type')
    
    if not page_id:
        return jsonify({'error': 'Page ID is required'}), 400
    
    # Get visitor ID from cookie
    visitor_id = get_visitor_id(request)
    
    # Get variant for visitor
    variant_info = get_variant_for_visitor(page_id, visitor_id, test_type)
    
    if not variant_info:
        return jsonify({'active_test': False})
    
    return jsonify({
        'active_test': True,
        'test_id': variant_info['test_id'],
        'test_type': variant_info['test_type'],
        'variant_id': variant_info['variant_id'],
        'content_version_id': variant_info['content_version_id']
    })

@bp.route('/api/test/conversion', methods=['POST'])
def record_test_conversion():
    """API endpoint to record a conversion."""
    test_id = request.json.get('test_id')
    variant_id = request.json.get('variant_id')
    
    if not test_id or not variant_id:
        return jsonify({'error': 'Test ID and variant ID are required'}), 400
    
    # Get visitor ID from cookie
    visitor_id = get_visitor_id(request)
    
    # Record conversion
    conversion = record_conversion(test_id, variant_id, visitor_id)
    
    if conversion:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'reason': 'Already converted'})