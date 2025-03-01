from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.auth.models import User
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm
from datetime import datetime
from functools import wraps

def admin_required(f):
    """
    Decorator for routes that require admin access.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def marketer_required(f):
    """
    Decorator for routes that require marketer access (admin or marketer).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_marketer():
            flash('You need marketer privileges to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('content.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('content.dashboard')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    """Register a new user (admin only)."""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {form.username.data} has been registered!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/register.html', title='Register User', form=form)

@bp.route('/users')
@login_required
@admin_required
def users():
    """List all users (admin only)."""
    users = User.query.all()
    return render_template('auth/users.html', title='User Management', users=users)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow users to change their password."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('content.dashboard'))
    
    return render_template('auth/change_password.html', form=form)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('auth.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('auth.users'))

@bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit a user's role (admin only)."""
    user = User.query.get_or_404(user_id)
    
    # Simple form just for changing role
    if request.method == 'POST':
        role = request.form.get('role')
        if role in ['admin', 'marketer', 'analytics']:
            user.role = role
            db.session.commit()
            flash(f'User {user.username} has been updated.', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/edit_user.html', user=user)
