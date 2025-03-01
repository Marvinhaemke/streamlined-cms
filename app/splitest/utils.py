from app import db
from app.content.models import ContentVersion
from app.splitest.models import SplitTest, TestVariant
from app.analytics.models import VisitorSession, Conversion
from app.utils import get_visitor_id  # Import from common utils
import random
import math
from datetime import datetime
import numpy as np
from scipy import stats

def create_split_test(page_id, name, test_type, goal_page_id, user_id):
    """
    Create a new split test.
    
    Args:
        page_id (int): ID of the page to test
        name (str): Name for the test
        test_type (str): 'design' or 'content'
        goal_page_id (int): ID of the conversion goal page
        user_id (int): ID of the user creating the test
        
    Returns:
        SplitTest: Created SplitTest instance
    """
    split_test = SplitTest(
        page_id=page_id,
        name=name,
        test_type=test_type,
        goal_page_id=goal_page_id,
        created_by=user_id
    )
    
    db.session.add(split_test)
    db.session.commit()
    
    return split_test

def add_variant(test_id, name, content_version_id, weight=1):
    """
    Add a variant to a split test.
    
    Args:
        test_id (int): ID of the split test
        name (str): Variant name
        content_version_id (int): ID of the content version
        weight (int): Traffic weight
        
    Returns:
        TestVariant: Created TestVariant instance
    """
    variant = TestVariant(
        test_id=test_id,
        name=name,
        content_version_id=content_version_id,
        weight=weight
    )
    
    db.session.add(variant)
    db.session.commit()
    
    return variant

def assign_variant(test_id, visitor_id):
    """
    Assign a visitor to a variant based on test weights.
    
    Args:
        test_id (int): ID of the split test
        visitor_id (str): Visitor ID
        
    Returns:
        TestVariant: Assigned TestVariant instance
    """
    # Check if visitor already assigned to this test
    visitor_session = VisitorSession.query.filter_by(
        split_test_id=test_id,
        visitor_id=visitor_id
    ).first()
    
    if visitor_session:
        return visitor_session.variant
    
    # Get all variants for this test
    variants = TestVariant.query.filter_by(test_id=test_id).all()
    
    if not variants:
        return None
    
    # Build weighted distribution
    weights = [v.weight for v in variants]
    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]
    
    # Select variant based on weights
    selected_variant = random.choices(variants, probabilities)[0]
    
    # Record visitor session
    visitor_session = VisitorSession(
        split_test_id=test_id,
        variant_id=selected_variant.id,
        visitor_id=visitor_id
    )
    db.session.add(visitor_session)
    db.session.commit()
    
    return selected_variant

def record_conversion(test_id, variant_id, visitor_id):
    """
    Record a conversion for a visitor in a split test.
    
    Args:
        test_id (int): ID of the split test
        variant_id (int): ID of the variant
        visitor_id (str): Visitor ID
        
    Returns:
        Conversion: Created Conversion instance or None if already converted
    """
    # Check if visitor has already converted
    existing = Conversion.query.filter_by(
        split_test_id=test_id,
        visitor_id=visitor_id
    ).first()
    
    if existing:
        return None
    
    # Record conversion
    conversion = Conversion(
        split_test_id=test_id,
        variant_id=variant_id,
        visitor_id=visitor_id
    )
    db.session.add(conversion)
    db.session.commit()
    
    return conversion

def calculate_statistical_significance(test_id):
    """
    Calculate statistical significance for a split test.
    
    Args:
        test_id (int): ID of the split test
        
    Returns:
        dict: Dictionary with statistical significance data
    """
    test = SplitTest.query.get(test_id)
    if not test:
        return None
    
    variants = test.variants.all()
    if len(variants) < 2:
        return None
    
    results = []
    for variant in variants:
        visitors = variant.visitor_sessions.count()
        conversions = variant.conversions.count()
        
        if visitors == 0:
            continue
        
        conversion_rate = (conversions / visitors) * 100
        results.append({
            'variant_id': variant.id,
            'name': variant.name,
            'visitors': visitors,
            'conversions': conversions,
            'conversion_rate': conversion_rate
        })
    
    if len(results) < 2:
        return results
    
    # Calculate confidence intervals and p-value
    for i, result in enumerate(results):
        n = result['visitors']
        p = result['conversion_rate'] / 100
        
        # Wilson score interval for binomial proportion
        z = 1.96  # 95% confidence
        denominator = 1 + z**2/n
        centre_adjusted_probability = p + z*z/(2*n)
        adjusted_standard_deviation = math.sqrt((p*(1-p) + z*z/(4*n))/n)
        
        lower_bound = (centre_adjusted_probability - z*adjusted_standard_deviation) / denominator * 100
        upper_bound = (centre_adjusted_probability + z*adjusted_standard_deviation) / denominator * 100
        
        result['confidence_interval'] = [lower_bound, upper_bound]
        
        # Compare with control (first variant)
        if i > 0:
            control = results[0]
            # Chi-squared test for independence
            observed = np.array([
                [result['conversions'], result['visitors'] - result['conversions']],
                [control['conversions'], control['visitors'] - control['conversions']]
            ])
            _, p_value, _, _ = stats.chi2_contingency(observed)
            result['p_value'] = p_value
            result['significant'] = p_value < 0.05  # 95% confidence level
    
    return results

def get_active_test_for_page(page_id, test_type=None):
    """
    Get the active split test for a page.
    
    Args:
        page_id (int): ID of the page
        test_type (str, optional): Type of test to filter by
        
    Returns:
        SplitTest: Active SplitTest instance or None
    """
    query = SplitTest.query.filter_by(page_id=page_id, is_active=True)
    
    if test_type:
        query = query.filter_by(test_type=test_type)
    
    return query.first()

def get_variant_for_visitor(page_id, visitor_id, test_type=None):
    """
    Get the assigned variant for a visitor on a page.
    
    Args:
        page_id (int): ID of the page
        visitor_id (str): Visitor ID
        test_type (str, optional): Type of test to filter by
        
    Returns:
        dict: Dictionary with test and variant info or None
    """
    # Get active test for this page
    test = get_active_test_for_page(page_id, test_type)
    
    if not test:
        return None
    
    # Assign or get variant for visitor
    variant = assign_variant(test.id, visitor_id)
    
    if not variant:
        return None
    
    return {
        'test_id': test.id,
        'test_name': test.name,
        'test_type': test.test_type,
        'variant_id': variant.id,
        'variant_name': variant.name,
        'content_version_id': variant.content_version_id
    }