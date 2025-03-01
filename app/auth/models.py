from app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    
    Attributes:
        id (int): Primary key for the user
        username (str): Unique username
        email (str): Unique email address
        password_hash (str): Hashed password
        role (str): User role (admin, marketer, analytics)
        created_at (datetime): Account creation timestamp
        last_login (datetime): Last login timestamp
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='analytics')  # admin, marketer, analytics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if the user has admin role."""
        return self.role == 'admin'
    
    def is_marketer(self):
        """Check if the user has marketer role."""
        return self.role == 'marketer' or self.role == 'admin'
    
    def is_analytics(self):
        """Check if the user has analytics role."""
        # All roles can view analytics
        return True
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Load a user given the user ID."""
    return User.query.get(int(user_id))
