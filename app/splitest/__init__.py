from flask import Blueprint

bp = Blueprint('splitest', __name__)

from app.splitest import routes
