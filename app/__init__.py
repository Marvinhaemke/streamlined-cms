from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_admin import Admin
from flask_ckeditor import CKEditor

import os
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
bcrypt = Bcrypt()
csrf = CSRFProtect()
admin = Admin(name='Streamlined CMS', template_mode='bootstrap4')
ckeditor = CKEditor()

def create_app(config_name='default'):
    """
    Create and configure the Flask application.
    
    Args:
        config_name (str): The configuration to use (default, development, testing, production)
        
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure the websites directory exists
    websites_dir = app.config['WEBSITES_DIRECTORY']
    if not os.path.exists(websites_dir):
        os.makedirs(websites_dir)
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    admin.init_app(app)
    ckeditor.init_app(app)
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.content import bp as content_bp
    app.register_blueprint(content_bp, url_prefix='/content')
    
    from app.splitest import bp as splitest_bp
    app.register_blueprint(splitest_bp, url_prefix='/splitest')
    
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Register shell context
    @app.shell_context_processor
    def make_shell_context():
        # Import models inside the function to avoid circular imports
        from app.auth.models import User
        from app.content.models import Website, Page
        from app.splitest.models import SplitTest, TestVariant
        
        return {
            'db': db, 
            'User': User, 
            'Website': Website, 
            'Page': Page,
            'SplitTest': SplitTest,
            'TestVariant': TestVariant
        }
    
    return app

# Don't import models here to avoid circular imports
# These imports will be handled in the shell_context_processor