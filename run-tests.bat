@echo off
echo Installing pytest-html if not already installed...
pip install pytest-html

echo Running tests and generating HTML report...
pytest --html=tests\test_report.html --self-contained-html

echo HTML test report saved to tests\test_report.html
