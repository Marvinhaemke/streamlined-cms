"""
Common utility functions shared across modules.
"""

import uuid
from flask import request, make_response

def get_visitor_id(req=None):
    """
    Get or create a visitor ID from cookies.
    
    Args:
        req: Flask request object (optional, defaults to global request)
        
    Returns:
        str: Visitor ID
    """
    if req is None:
        req = request
        
    visitor_id = req.cookies.get('visitor_id')
    
    # If visitor ID doesn't exist, create a new one
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        
        # Only set cookie if we have a response object (not in tests)
        if hasattr(make_response, '__call__'):
            response = make_response()
            response.set_cookie('visitor_id', visitor_id, max_age=60*60*24*365)  # 1 year
        
    return visitor_id