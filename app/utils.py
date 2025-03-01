"""
Common utility functions shared across modules.
"""

import uuid

def get_visitor_id(request):
    """
    Get or create a visitor ID from cookies.
    
    Args:
        request: Flask request object
        
    Returns:
        str: Visitor ID
    """
    from flask import request, make_response
    
    visitor_id = request.cookies.get('visitor_id')
    
    # If visitor ID doesn't exist, create a new one
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        response = make_response()
        response.set_cookie('visitor_id', visitor_id, max_age=60*60*24*365)  # 1 year
        
    return visitor_id
