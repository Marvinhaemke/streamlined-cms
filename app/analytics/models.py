from app import db
from datetime import datetime

class VisitorSession(db.Model):
    """
    VisitorSession model tracks visitor assignments to test variants.
    
    Attributes:
        id (int): Primary key
        split_test_id (int): Foreign key to SplitTest
        variant_id (int): Foreign key to TestVariant
        visitor_id (str): Unique visitor identifier
        user_agent (str): Browser user agent
        ip_address (str): Visitor IP address (anonymized)
        referrer (str): Referrer URL
        created_at (datetime): Creation timestamp
    """
    __tablename__ = 'visitor_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    split_test_id = db.Column(db.Integer, db.ForeignKey('split_tests.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('test_variants.id'), nullable=False)
    visitor_id = db.Column(db.String(64), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars
    referrer = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VisitorSession {self.id} for Test {self.split_test_id}>'


class Conversion(db.Model):
    """
    Conversion model tracks goal completions in tests.
    
    Attributes:
        id (int): Primary key
        split_test_id (int): Foreign key to SplitTest
        variant_id (int): Foreign key to TestVariant
        visitor_id (str): Unique visitor identifier
        created_at (datetime): Creation timestamp
    """
    __tablename__ = 'conversions'
    
    id = db.Column(db.Integer, primary_key=True)
    split_test_id = db.Column(db.Integer, db.ForeignKey('split_tests.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('test_variants.id'), nullable=False)
    visitor_id = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Conversion {self.id} for Test {self.split_test_id}>'


class PageView(db.Model):
    """
    PageView model tracks individual page views.
    
    Attributes:
        id (int): Primary key
        page_id (int): Foreign key to Page
        visitor_id (str): Unique visitor identifier
        user_agent (str): Browser user agent
        ip_address (str): Visitor IP address (anonymized)
        referrer (str): Referrer URL
        created_at (datetime): Creation timestamp
    """
    __tablename__ = 'page_views'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    visitor_id = db.Column(db.String(64), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    referrer = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    page = db.relationship('Page', backref='page_views')
    
    def __repr__(self):
        return f'<PageView {self.id} for Page {self.page_id}>'
