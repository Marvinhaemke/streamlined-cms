import os
import shutil
import json
import re
from bs4 import BeautifulSoup
from flask import current_app
from werkzeug.utils import secure_filename
from app import db
from app.content.models import ContentVersion

def create_website_directory(website):
    """
    Create a directory for a website in the configured websites folder.
    
    Args:
        website: Website model instance
        
    Returns:
        str: The path to the created directory
    """
    directory_path = website.file_path
    
    # Create directory if it doesn't exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    return directory_path

def save_uploaded_file(file, path):
    """
    Save an uploaded file to the specified path.
    
    Args:
        file: File object from Flask request.files
        path: Directory path where the file should be saved
        
    Returns:
        str: The saved file path
    """
    filename = secure_filename(file.filename)
    # Create directory if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)
    
    file_path = os.path.join(path, filename)
    file.save(file_path)
    return file_path

def parse_html_content(html_content):
    """
    Parse HTML content to extract editable elements.
    
    Args:
        html_content (str): HTML content to parse
        
    Returns:
        dict: Dictionary of element IDs/selectors and their text content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    content_dict = {}
    
    # Extract text from elements with IDs
    for element in soup.find_all(id=True):
        if element.string:
            content_dict[f"#{element['id']}"] = element.string.strip()
    
    # Extract text from elements with specific classes
    for element in soup.find_all(class_=True):
        for cls in element['class']:
            if cls.startswith('editable-'):
                content_dict[f".{cls}"] = element.get_text().strip()
    
    # Extract text from elements with data-editable attribute
    for element in soup.find_all(attrs={"data-editable": True}):
        selector = f"[data-editable='{element['data-editable']}']"
        content_dict[selector] = element.get_text().strip()
    
    return content_dict

def apply_content_changes(html_content, content_changes):
    """
    Apply content changes to HTML.
    
    Args:
        html_content (str): Original HTML content
        content_changes (dict): Dictionary of selectors and new content
        
    Returns:
        str: Modified HTML content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for selector, new_content in content_changes.items():
        # Handle ID selectors
        if selector.startswith('#'):
            element_id = selector[1:]
            element = soup.find(id=element_id)
            if element:
                element.string = new_content
        
        # Handle class selectors
        elif selector.startswith('.'):
            class_name = selector[1:]
            elements = soup.find_all(class_=class_name)
            for element in elements:
                element.string = new_content
        
        # Handle attribute selectors
        elif selector.startswith('['):
            # Extract attribute name and value from selector
            match = re.match(r'\[([^=]+)=[\'"]([^\'"]+)[\'"]\]', selector)
            if match:
                attr_name, attr_value = match.groups()
                elements = soup.find_all(attrs={attr_name: attr_value})
                for element in elements:
                    element.string = new_content
    
    return str(soup)

def inject_editor_script(html_content, page_id):
    """
    Inject the editor script into HTML content.
    
    Args:
        html_content (str): Original HTML content
        page_id (int): ID of the page
        
    Returns:
        str: HTML content with editor script injected
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Create script tag
    script = soup.new_tag('script')
    script['src'] = f'/static/js/editor.js'
    script['data-page-id'] = str(page_id)
    
    # Add to head or create head if it doesn't exist
    if soup.head:
        soup.head.append(script)
    else:
        head = soup.new_tag('head')
        head.append(script)
        soup.html.insert(0, head)
    
    return str(soup)

def get_page_html(page):
    """
    Get the HTML content for a page.
    
    Args:
        page: Page model instance
        
    Returns:
        str: HTML content of the page
    """
    # For testing purposes, if the file doesn't exist, generate a dummy HTML
    if not os.path.exists(page.file_path):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{page.title}</title>
        </head>
        <body>
            <h1 id="title">Welcome to {page.title}</h1>
            <div id="content">This is a placeholder content for {page.title}.</div>
        </body>
        </html>
        """
    
    try:
        with open(page.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        current_app.logger.error(f"Error reading page file: {e}")
        return ""

def save_page_html(page, html_content):
    """
    Save HTML content to a page file.
    
    Args:
        page: Page model instance
        html_content (str): HTML content to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(page.file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(page.file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return True
    except Exception as e:
        current_app.logger.error(f"Error saving page file: {e}")
        return False

def create_content_version(page, content, version_type, user_id):
    """
    Create a new content version for a page.
    
    Args:
        page: Page model instance
        content: Content to save (dict or str)
        version_type (str): 'content' or 'design'
        user_id (int): ID of the user creating the version
        
    Returns:
        ContentVersion: Created ContentVersion instance
    """
    # Generate content hash
    content_hash = ContentVersion.generate_content_hash(content)
    
    # Check if identical content version already exists
    existing = ContentVersion.query.filter_by(
        page_id=page.id, 
        content_hash=content_hash,
        version_type=version_type
    ).first()
    
    if existing:
        return existing
    
    # Create new content version
    content_version = ContentVersion(
        page_id=page.id,
        content_hash=content_hash,
        version_type=version_type,
        created_by=user_id
    )
    
    # Set content based on version type
    if version_type == 'content':
        if isinstance(content, dict):
            content_version.content_json = json.dumps(content)
        else:
            content_version.content_json = content
    else:  # design version
        content_version.content_html = content
    
    db.session.add(content_version)
    db.session.commit()
    
    return content_version

def activate_content_version(content_version):
    """
    Activate a content version and deactivate all others for the page.
    
    Args:
        content_version: ContentVersion model instance
        
    Returns:
        bool: True if successful
    """
    # Deactivate all other versions for this page
    ContentVersion.query.filter_by(page_id=content_version.page_id).update({'is_active': False})
    
    # Activate this version
    content_version.is_active = True
    db.session.commit()
    
    return True