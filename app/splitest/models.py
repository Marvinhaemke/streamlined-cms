from app import db
from datetime import datetime
import json

class SplitTest(db.Model):
    """
    SplitTest model represents an A/B test.
    
    Attributes:
        id (int): Primary key
        page_id (int): Foreign key to Page
        name (str): Test name
        test_type (str): Type of test ('design' or 'content')
        goal_page_id (int): ID of the page considered as conversion
        is_active (bool): Whether the test is currently running
        created_by (int): User ID who created the test
        start_date (datetime): Test start date
        end_date (datetime): Test end date or null if ongoing
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = 'split_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    test_type = db.Column(db.String(20), nullable=False)  # 'design' or 'content'
    goal_page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - explicitly specify foreign keys
    creator = db.relationship('User', backref='split_tests')
    variants = db.relationship('TestVariant', backref='split_test', lazy='dynamic', 
                              cascade='all, delete-orphan')
    # Specify which foreign key to use for each relationship
    page = db.relationship('Page', foreign_keys=[page_id], backref='split_tests')
    goal_page = db.relationship('Page', foreign_keys=[goal_page_id])
    
    visitor_sessions = db.relationship('VisitorSession', backref='split_test', lazy='dynamic')
    conversions = db.relationship('Conversion', backref='split_test', lazy='dynamic')
    
    def __repr__(self):
        return f'<SplitTest {self.name} for Page {self.page_id}>'
    
    @property
    def total_visitors(self):
        """Get the total number of visitors for this test."""
        return self.visitor_sessions.count()
    
    @property
    def total_conversions(self):
        """Get the total number of conversions for this test."""
        return self.conversions.count()
    
    @property
    def conversion_rate(self):
        """Get the overall conversion rate for this test."""
        visitors = self.total_visitors
        if visitors == 0:
            return 0
        return (self.total_conversions / visitors) * 100
    
    def get_variant_stats(self):
        """Get conversion statistics for each variant."""
        stats = []
        for variant in self.variants:
            visitors = variant.visitor_sessions.count()
            conversions = variant.conversions.count()
            conversion_rate = 0
            if visitors > 0:
                conversion_rate = (conversions / visitors) * 100
            
            stats.append({
                'variant_id': variant.id,
                'name': variant.name,
                'visitors': visitors,
                'conversions': conversions,
                'conversion_rate': conversion_rate
            })
        
        return stats


class TestVariant(db.Model):
    """
    TestVariant model represents a variant in a split test.
    
    Attributes:
        id (int): Primary key
        test_id (int): Foreign key to SplitTest
        name (str): Variant name
        content_version_id (int): Foreign key to ContentVersion
        weight (int): Traffic weight for variant assignment
        created_at (datetime): Creation timestamp
    """
    __tablename__ = 'test_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('split_tests.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    content_version_id = db.Column(db.Integer, db.ForeignKey('content_versions.id'), nullable=False)
    weight = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    content_version = db.relationship('ContentVersion')
    visitor_sessions = db.relationship('VisitorSession', backref='variant', lazy='dynamic')
    conversions = db.relationship('Conversion', backref='variant', lazy='dynamic')
    
    def __repr__(self):
        return f'<TestVariant {self.name} for Test {self.test_id}>'