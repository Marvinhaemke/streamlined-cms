import os
from app import create_app, db
from dotenv import load_dotenv

load_dotenv()

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.cli.command('create-admin')
def create_admin():
    """Create an admin user."""
    from app.auth.models import User
    from getpass import getpass
    
    username = input('Admin username: ')
    email = input('Admin email: ')
    password = getpass('Admin password: ')
    password_confirm = getpass('Confirm password: ')
    
    if password != password_confirm:
        print('Passwords do not match.')
        return
    
    user = User(username=username, email=email, role='admin')
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    print(f'Admin user {username} created successfully.')

if __name__ == '__main__':
    app.run(debug=True)