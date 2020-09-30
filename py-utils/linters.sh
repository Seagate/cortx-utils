python3 -m pylint --version
python3 -m flake8 --version
find . -type f -name "*.py" | xargs python3 -m pylint
python3 -m flake8 .