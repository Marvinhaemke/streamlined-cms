from app import db
from datetime import datetime
import os
import hashlib
import json
from werkzeug.utils import secure_filename

class Website(db.Model):
    """
    Website model represents a hosted website.
    
    Attributes:
        id (int): Primary key
        name (str): Human-readable name for the website
        domain (str): Domain or subdomain for the website
        directory (str): Directory path where files are stored
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = 'websites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), unique=True, nullable=False)
    directory = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pages = db.relationship('Page', backref='website', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def file_path(self):
        """Get the full file path for this website's directory."""
        from flask import current_app
        return os.path.join(current_app.config['WEBSITES_DIRECTORY'], self.directory)
    
    def __repr__(self):
        return f'<Website {self.name}>'


class Page(db.Model):
    """
    Page model represents a specific page within a website.
    
    Attributes:
        id (int): Primary key
        website_id (int): Foreign key to Website
        path (str): URL path for the page (relative to domain)
        title (str): Page title
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    content_versions = db.relationship('ContentVersion', backref='page', lazy='dynamic', 
                                       cascade='all, delete-orphan')
    # The split_tests relationship is now defined in the SplitTest model with explicitly defined foreign keys
    # No need to define it here to avoid the ambiguity
    
    __table_args__ = (
        db.UniqueConstraint('website_id', 'path', name='uix_website_path'),
    )
    
    @property
    def file_path(self):
        """Get the full file path for this page."""
        return os.path.join(self.website.file_path, self.path.lstrip('/'))
    
    @property
    def url(self):
        """Get the full URL for this page."""
        return f"https://{self.website.domain}/{self.path.lstrip('/')}"
    
    @property
    def active_version(self):
        """Get the currently active content version."""
        return self.content_versions.filter_by(is_active=True).first()
    
    def __repr__(self):
        return f'<Page {self.website.domain}/{self.path}>'


class ContentVersion(db.Model):
    """
    ContentVersion model stores different versions of a page's content.
    
    Attributes:
        id (int): Primary key
        page_id (int): Foreign key to Page
        content_hash (str): Hash of the content for quick comparison
        content_json (str): JSON representation of content changes
        content_html (str): Full HTML content (for design variants)
        version_type (str): 'content' for text/image changes, 'design' for full HTML
        created_by (int): User ID who created this version
        is_active (bool): Whether this is the active version
        created_at (datetime): Creation timestamp
    """
    __tablename__ = 'content_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    content_json = db.Column(db.Text, nullable=True)  # For content variants (text/images)
    content_html = db.Column(db.Text, nullable=True)  # For design variants (full HTML)
    version_type = db.Column(db.String(20), default='content')  # 'content' or 'design'
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='content_versions')
    
    def __repr__(self):
        return f'<ContentVersion {self.id} for Page {self.page_id}>'
    
    @staticmethod
    def generate_content_hash(content):
        """Generate a hash for the content."""
        if isinstance(content, dict):
            content = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_content(self):
        """Get the content based on version type."""
        if self.version_type == 'content':
            return json.loads(self.content_json) if self.content_json else {}
        return self.content_html