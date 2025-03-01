@echo off
echo Running tests and generating text report...
pytest --verbose > tests\test_report.txt

echo Text test report saved to tests\test_report.txt
