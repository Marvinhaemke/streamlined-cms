# Streamlined CMS (Very Early Development Prototype/not yet usable)

A simple, lightweight content management system that allows marketers to easily edit website content and run split tests without developer intervention.

## Features

- **Content Management**: Easy editing of text and images on any website
- **Split Testing**: A/B testing of both content (text/images) and design (different HTML)
- **Analytics**: Track visitors, conversions, and test performance
- **Security**: Role-based access control and proper authentication
- **Flexibility**: Works with any HTML/CSS/JS website

## Installation

### Requirements

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### Setup

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
```

4. Set up environment variables:

Create a `.env` file in the project root with the following content:

```
FLASK_APP=run.py
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
WEBSITES_DIRECTORY=websites
```

Replace `your-secret-key-here` with a secure random string.

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

Follow the prompts to create the admin account.

7. Run the application:

```bash
flask run
```

The application will be available at http://127.0.0.1:5000/

## Project Structure

```
streamlined-cms/
├── app/                      # Main application package
│   ├── __init__.py           # Application factory
│   ├── auth/                 # Authentication functionality
│   ├── content/              # Content management
│   ├── splitest/             # Split testing
│   ├── analytics/            # Analytics and tracking
│   ├── static/               # Static assets
│   └── templates/            # HTML templates
├── migrations/               # Database migrations
├── tests/                    # Test suite
├── config.py                 # Configuration settings
├── requirements.txt          # Dependencies
└── run.py                    # Application entry point
```

## Usage

### Managing Websites

1. Log in with your admin account
2. Go to the Dashboard
3. Click "Add Website" and enter the website details
4. Upload website files using the "Upload Files" button

### Editing Content

1. Navigate to a page in the CMS
2. Click "Edit Content"
3. Make changes to the text and images
4. Click "Save Changes"

### Creating Split Tests

1. Navigate to a page in the CMS
2. Go to "Split Tests" tab
3. Click "New Split Test"
4. Enter test details and select the goal page
5. Add variants with different content versions
6. Start the test

### Viewing Analytics

1. Go to the Analytics dashboard
2. View overall statistics for websites and pages
3. Check detailed results for split tests

## Running Tests

### Setup Testing Environment

1. Make sure you have pytest installed:

```bash
pip install pytest pytest-flask
```

2. Run all tests:

```bash
pytest
```

3. Run specific test modules:

```bash
pytest tests/test_auth.py
pytest tests/test_content.py
pytest tests/test_splitest.py
pytest tests/test_analytics.py
```

4. Generate a coverage report:

```bash
pytest --cov=app tests/
```

### Testing Strategy

Our test suite includes:

1. **Unit Tests**: Testing individual functions and components in isolation
2. **Integration Tests**: Testing interactions between components
3. **End-to-End Tests**: Testing complete user workflows

Each module has its own test file:

- `test_auth.py`: Authentication functionality
- `test_content.py`: Content management features
- `test_splitest.py`: Split testing functionality
- `test_analytics.py`: Analytics tracking and reporting
- `test_integration.py`: Cross-module integration tests

## Troubleshooting

### Common Issues

1. **Database errors**:
   - Make sure you've run the migrations
   - Check the database connection string in your `.env` file

2. **File upload issues**:
   - Ensure the `WEBSITES_DIRECTORY` exists and is writable
   - Check file permissions

3. **Split tests not working**:
   - Ensure you have at least two variants
   - Verify the tracking script is loaded on your pages

### Debug Mode

To enable more detailed error messages, set:

```
FLASK_ENV=development
```

in your `.env` file.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
