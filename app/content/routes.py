from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.content import bp
from app.content.models import Website, Page, ContentVersion
from app.auth.routes import admin_required, marketer_required
from app.content.utils import (create_website_directory, save_uploaded_file, parse_html_content,
                             apply_content_changes, inject_editor_script, get_page_html,
                             save_page_html, create_content_version, activate_content_version)
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import re

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard showing all websites."""
    websites = Website.query.all()
    return render_template('content/dashboard.html', title='Dashboard', websites=websites)

# Updated routes to match what tests expect
@bp.route('/website/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_website():
    """Create a new website."""
    if request.method == 'POST':
        name = request.form.get('name')
        domain = request.form.get('domain')
        
        if not name or not domain:
            flash('Name and domain are required', 'danger')
            return redirect(url_for('content.new_website'))
        
        # Sanitize domain
        domain = domain.lower().strip()
        
        # Check if domain already exists
        if Website.query.filter_by(domain=domain).first():
            flash(f'Domain {domain} already exists', 'danger')
            return redirect(url_for('content.new_website'))
        
        # Create directory name from domain
        directory = re.sub(r'[^a-z0-9]', '_', domain)
        
        # Create website in database
        website = Website(name=name, domain=domain, directory=directory)
        db.session.add(website)
        db.session.commit()
        
        # Create directory for website
        create_website_directory(website)
        
        flash(f'Website {name} created successfully', 'success')
        return redirect(url_for('content.dashboard'))
    
    return render_template('content/new_website.html', title='New Website')

# Add route for content module but using the expected URL path
@bp.route('/website/<int:website_id>')
@login_required
def website_detail(website_id):
    """Show website details and pages."""
    website = Website.query.get_or_404(website_id)
    pages = website.pages.all()
    return render_template('content/website_detail.html', title=website.name, website=website, pages=pages)

@bp.route('/website/<int:website_id>/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_website_files(website_id):
    """Upload files for a website."""
    website = Website.query.get_or_404(website_id)
    
    if request.method == 'POST':
        # Check if files were uploaded
        if 'files[]' not in request.files:
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files[]')
        path = request.form.get('path', '')
        
        # Sanitize path
        path = path.lstrip('/')
        
        # Determine upload directory
        upload_dir = os.path.join(website.file_path, path)
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_count = 0
        for file in files:
            if file.filename:
                try:
                    # Save file
                    save_uploaded_file(file, upload_dir)
                    file_count += 1
                    
                    # If this is an HTML file, check if we need to create a page for it
                    if file.filename.endswith('.html'):
                        file_path = os.path.join(path, file.filename)
                        # Check if page already exists
                        page = Page.query.filter_by(website_id=website.id, path=file_path).first()
                        if not page:
                            # Create page
                            page_title = file.filename.replace('.html', '').title()
                            page = Page(website_id=website.id, path=file_path, title=page_title)
                            db.session.add(page)
                            db.session.commit()
                except Exception as e:
                    current_app.logger.error(f"Error uploading file: {e}")
                    flash(f'Error uploading {file.filename}: {str(e)}', 'danger')
        
        if file_count > 0:
            flash(f'{file_count} files uploaded successfully', 'success')
        
        return redirect(url_for('content.website_detail', website_id=website.id))
    
    return render_template('content/upload_files.html', title='Upload Files', website=website)

# Added route for page_detail in the expected URL path 
@bp.route('/page/<int:page_id>')
@login_required
def page_detail(page_id):
    """Show page details and content versions."""
    page = Page.query.get_or_404(page_id)
    content_versions = page.content_versions.order_by(ContentVersion.created_at.desc()).all()
    
    return render_template('content/page_detail.html', title=page.title, page=page, content_versions=content_versions)

# Add route in the expected URL path
@bp.route('/page/new/<int:website_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def new_page(website_id):
    """Create a new page."""
    website = Website.query.get_or_404(website_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        path = request.form.get('path')
        
        if not title or not path:
            flash('Title and path are required', 'danger')
            return redirect(url_for('content.new_page', website_id=website.id))
        
        # Ensure path starts with a slash
        if not path.startswith('/'):
            path = '/' + path
        
        # Check if page already exists
        if Page.query.filter_by(website_id=website.id, path=path).first():
            flash(f'Page with path {path} already exists', 'danger')
            return redirect(url_for('content.new_page', website_id=website.id))
        
        # Create page
        page = Page(website_id=website.id, path=path, title=title)
        db.session.add(page)
        db.session.commit()
        
        flash(f'Page {title} created successfully', 'success')
        return redirect(url_for('content.website_detail', website_id=website.id))
    
    return render_template('content/new_page.html', title='New Page', website=website)

@bp.route('/page/<int:page_id>/edit')
@login_required
@marketer_required
def edit_page(page_id):
    """Edit page content using WYSIWYG editor."""
    page = Page.query.get_or_404(page_id)
    
    # Get HTML content
    html_content = get_page_html(page)
    
    if not html_content:
        flash('Could not read page content', 'danger')
        return redirect(url_for('content.page_detail', page_id=page.id))
    
    # Inject editor script
    html_with_editor = inject_editor_script(html_content, page.id)
    
    # Render content in iframe
    return render_template('content/edit_page.html', title=f'Edit {page.title}', page=page, content=html_with_editor)

@bp.route('/api/page/<int:page_id>/content', methods=['GET'])
@login_required
@marketer_required
def get_page_content(page_id):
    """API endpoint to get page content for editor."""
    page = Page.query.get_or_404(page_id)
    
    # Get HTML content
    html_content = get_page_html(page)
    
    if not html_content:
        return jsonify({'error': 'Could not read page content'}), 500
    
    # Parse editable content
    content_dict = parse_html_content(html_content)
    
    # Get current content version if exists
    active_version = page.active_version
    if active_version and active_version.version_type == 'content':
        try:
            content_changes = json.loads(active_version.content_json)
            # Apply changes to content_dict
            content_dict.update(content_changes)
        except:
            pass
    
    return jsonify({'content': content_dict})

@bp.route('/api/page/<int:page_id>/content', methods=['POST'])
@login_required
@marketer_required
def save_page_content(page_id):
    """API endpoint to save page content changes."""
    page = Page.query.get_or_404(page_id)
    
    try:
        content_changes = request.json.get('content', {})
        
        if not content_changes:
            return jsonify({'error': 'No content changes provided'}), 400
        
        # Create new content version
        content_version = create_content_version(page, content_changes, 'content', current_user.id)
        
        # Activate the version
        activate_content_version(content_version)
        
        return jsonify({'success': True, 'version_id': content_version.id})
    except Exception as e:
        current_app.logger.error(f"Error saving content: {e}")
        return jsonify({'error': f'Error saving content: {str(e)}'}), 500

@bp.route('/page/<int:page_id>/version/<int:version_id>/activate', methods=['POST'])
@login_required
@marketer_required
def activate_version(page_id, version_id):
    """Activate a specific content version."""
    page = Page.query.get_or_404(page_id)
    content_version = ContentVersion.query.get_or_404(version_id)
    
    # Verify version belongs to page
    if content_version.page_id != page.id:
        flash('Invalid content version', 'danger')
        return redirect(url_for('content.page_detail', page_id=page.id))
    
    # Activate version
    activate_content_version(content_version)
    
    flash('Content version activated successfully', 'success')
    return redirect(url_for('content.page_detail', page_id=page.id))

@bp.route('/serve/<path:domain>/<path:filepath>')
def serve_website(domain, filepath):
    """Serve website files."""
    # Find website by domain
    website = Website.query.filter_by(domain=domain).first_or_404()
    
    # Find if this is a page
    page_path = f'/{filepath}'
    page = Page.query.filter_by(website_id=website.id, path=page_path).first()
    
    if not page:
        # Serve static file
        return send_from_directory(website.file_path, filepath)
    
    # If user is logged in and has permission, inject editor script
    if current_user.is_authenticated and current_user.is_marketer():
        html_content = get_page_html(page)
        if html_content:
            html_with_editor = inject_editor_script(html_content, page.id)
            return html_with_editor
    
    # Get HTML content
    html_content = get_page_html(page)
    
    # Get active content version
    active_version = page.active_version
    
    # Apply content changes if exists
    if active_version and active_version.version_type == 'content':
        try:
            content_changes = json.loads(active_version.content_json)
            html_content = apply_content_changes(html_content, content_changes)
        except:
            pass
    
    return html_content