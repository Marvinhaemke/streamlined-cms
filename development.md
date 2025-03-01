# Development Guide for Streamlined CMS

This guide provides information for developers working on the Streamlined CMS project, covering architecture, coding standards, and development workflows.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Code Organization](#code-organization)
4. [Database Management](#database-management)
5. [Extending the CMS](#extending-the-cms)
6. [Frontend Development](#frontend-development)
7. [API Reference](#api-reference)
8. [Coding Standards](#coding-standards)
9. [Git Workflow](#git-workflow)

## Architecture Overview

Streamlined CMS follows a modular Flask application structure organized by feature:

- **Authentication Module (`auth/`)**: User management, login/logout, and permissions
- **Content Module (`content/`)**: Website and page management, content editing
- **Split Test Module (`splitest/`)**: A/B testing functionality
- **Analytics Module (`analytics/`)**: Tracking and reporting

The application uses:
- SQLAlchemy for database interactions
- Flask-Login for authentication
- Jinja2 for templating
- WYSIWYG editor for content editing
- Custom JavaScript for client-side tracking and editing

### Request Flow

1. User requests a page
2. Authentication middleware checks permissions
3. Route handlers process the request
4. Database queries retrieve necessary data
5. Templates render the HTML response
6. Client-side JavaScript enhances the experience

## Development Environment Setup

### Prerequisites

- Python 3.8+
- pip
- Git
- SQLite (for development)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/streamlined-cms.git
   cd streamlined-cms
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. Set up environment variables:
   Create a `.env` file with:
   ```
   FLASK_APP=run.py
   FLASK_CONFIG=development
   FLASK_DEBUG=1
   SECRET_KEY=dev-secret-key
   DATABASE_URL=sqlite:///app.db
   WEBSITES_DIRECTORY=websites
   ```

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate -m "Initial database"
   flask db upgrade
   ```

6. Create an admin user:
   ```bash
   flask create-admin
   ```

7. Run the development server:
   ```bash
   flask run
   ```

### Development Tools

- **Visual Studio Code**: Recommended IDE
- **SQLite Browser**: For viewing and editing the development database
- **Postman**: For testing API endpoints
- **Flask Debug Toolbar**: For debugging Flask applications

Add Flask-DebugToolbar to your project:
```bash
pip install Flask-DebugToolbar
```

Then add to your app:
```python
# In app/__init__.py
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension()

# In create_app function
toolbar.init_app(app)
```

## Code Organization

```
streamlined-cms/
├── app/                      # Main application package
│   ├── __init__.py           # Application factory
│   ├── auth/                 # Authentication module
│   │   ├── __init__.py
│   │   ├── models.py         # User models
│   │   ├── routes.py         # Auth routes
│   │   └── forms.py          # Login/registration forms
│   ├── content/              # Content management
│   │   ├── __init__.py
│   │   ├── models.py         # Website and page models
│   │   ├── routes.py         # Content routes
│   │   └── utils.py          # Content utilities
│   ├── splitest/            # Split testing
│   │   ├── __init__.py
│   │   ├── models.py         # Test and variant models
│   │   ├── routes.py         # Split test routes
│   │   └── utils.py          # Test utilities
│   ├── analytics/            # Analytics and tracking
│   │   ├── __init__.py
│   │   ├── models.py         # Analytics models
│   │   ├── routes.py         # Analytics routes
│   │   └── utils.py          # Analytics utilities
│   ├── static/               # Static assets
│   │   ├── css/              # Stylesheets
│   │   ├── js/               # JavaScript files
│   │   └── img/              # Images
│   └── templates/            # HTML templates
│       ├── auth/             # Auth templates
│       ├── content/          # Content templates
│       ├── splitest/         # Split test templates
│       └── analytics/        # Analytics templates
├── migrations/               # Database migrations
├── tests/                    # Test suite
│   ├── conftest.py           # Test configuration
│   ├── test_auth.py          # Auth tests
│   ├── test_content.py       # Content tests
│   ├── test_splitest.py      # Split test tests
│   └── test_analytics.py     # Analytics tests
├── config.py                 # Configuration settings
├── requirements.txt          # Dependencies
└── run.py                    # Application entry point
```

### Module Structure

Each module is organized with similar files:
- `__init__.py`: Blueprint definition
- `models.py`: Database models
- `routes.py`: Route handlers
- `utils.py`: Helper functions
- `forms.py`: WTForms definitions (if needed)

## Database Management

### Database Schema

![Database Schema](docs/images/db_schema.png)

Key relationships:
- Website has many Pages
- Page has many ContentVersions
- Page has many SplitTests
- SplitTest has many TestVariants
- TestVariant relates to ContentVersion

### Working with Migrations

Add a new migration:
```bash
flask db migrate -m "Description of changes"
```

Apply migrations:
```bash
flask db upgrade
```

Revert migrations:
```bash
flask db downgrade
```

### Database Best Practices

1. **Use SQLAlchemy properly**
   - Use relationships and backref appropriately
   - Define cascades for related deletions
   - Use query optimization when needed

2. **Keep migrations clean**
   - Review auto-generated migrations
   - Split complex schema changes into multiple migrations
   - Test migrations both up and down

3. **Model design**
   - Use meaningful column names
   - Add appropriate indexes
   - Define constraints and default values

## Extending the CMS

### Adding New Features

1. **Plan your feature**
   - Define requirements and acceptance criteria
   - Design the database schema changes
   - Plan the API endpoints

2. **Add database models**
   - Add models to the appropriate module
   - Create database migrations

3. **Implement routes and views**
   - Add route handlers
   - Create templates
   - Implement forms

4. **Add tests**
   - Unit tests for model methods
   - Route tests for new endpoints
   - Integration tests for feature interactions

### Adding a New Module

1. Create the module directory and files:
```
app/newmodule/
├── __init__.py
├── models.py
├── routes.py
└── utils.py
```

2. Define the blueprint in `__init__.py`:
```python
from flask import Blueprint

bp = Blueprint('newmodule', __name__)

from app.newmodule import routes
```

3. Register the blueprint in `app/__init__.py`:
```python
from app.newmodule import bp as newmodule_bp
app.register_blueprint(newmodule_bp, url_prefix='/newmodule')
```

## Frontend Development

### Templates

Templates use Jinja2 and follow this structure:
- Base template (`base.html`) with common layout
- Module-specific templates extending base
- Partial templates for reusable components

### Static Files

- CSS: `/static/css/`
- JavaScript: `/static/js/`
- Images: `/static/img/`

### JavaScript Components

1. **Editor (editor.js)**
   - Handles in-place content editing
   - Saves content changes via API

2. **Tracking (tracking.js)**
   - Records page views
   - Manages split test assignments
   - Tracks conversions

### WYSIWYG Editor Integration

The CMS uses CKEditor for content editing:
- Configuration in `app/__init__.py`
- Custom configuration in `app/static/js/ckeditor-config.js`
- Integration with content saving in `editor.js`

## API Reference

### Authentication

- `POST /auth/login`: Log in a user
- `GET /auth/logout`: Log out a user
- `POST /auth/register`: Register a new user (admin only)

### Content Management

- `GET /api/page/<id>/content`: Get page content
- `POST /api/page/<id>/content`: Save page content changes
- `GET /content/page/<id>`: Get page details

### Split Testing

- `GET /api/test/variant`: Get variant for a page and visitor
- `POST /api/test/conversion`: Record a conversion
- `GET /api/test/<id>`: Get test details

### Analytics

- `POST /api/page_view`: Record a page view
- `GET /analytics/export/test/<id>`: Export test data as CSV

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:
- 4 spaces for indentation
- 79 character line length
- Docstrings for all public functions, classes, and methods
- Type hints for function parameters and return values
- Use f-strings for string formatting

### JavaScript Style

- 2 space indentation
- Semicolons required
- ES6 features encouraged
- JSDoc comments for functions
- Prefer const/let over var

### General Practices

1. **Function size**
   - Keep functions small and focused
   - Follow single responsibility principle

2. **Error handling**
   - Use try/except blocks for potential failures
   - Log exceptions with appropriate context
   - Return clear error messages to users

3. **Comments and documentation**
   - Comment complex logic
   - Document public interfaces
   - Keep comments up to date with code changes

## Git Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Commit Message Format

```
<type>(<scope>): <short summary>

<detailed description>

<breaking changes>

<issue references>
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Formatting changes
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks

Example:
```
feat(auth): add password reset functionality

Adds endpoints and email sending for password reset.
Includes token generation and validation.

Closes #123
```

### Pull Request Process

1. Create a feature branch from develop
2. Implement changes with test coverage
3. Submit a pull request to develop
4. Ensure CI passes
5. Get code review approval
6. Merge to develop
7. Delete feature branch

### Release Process

1. Create a release branch from develop
2. Finalize documentation and version numbers
3. Fix any release blockers
4. Merge to main with version tag
5. Merge back to develop

## Appendix

### Useful Commands

```bash
# Run linter
flake8 app tests

# Run auto-formatter
black app tests

# Run type checking
mypy app

# Generate API documentation
sphinx-build -b html docs/source docs/build
```

### Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [CKEditor Documentation](https://ckeditor.com/docs/)
- [pytest Documentation](https://docs.pytest.org/)
