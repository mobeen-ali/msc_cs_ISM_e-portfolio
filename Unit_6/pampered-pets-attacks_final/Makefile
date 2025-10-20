.PHONY: install lint test run

# Install all Python dependencies
install:
	pip install -r requirements.txt

# Run the ruff linter
lint:
	ruff .

# Execute the unit tests
test:
	pytest -q

# Start the Flask development server
run:
	flask --app run run