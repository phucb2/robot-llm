# Description: Makefile for the project
debug:
	uvicorn --reload --log-level debug --reload-dir . app.main:app

unittest:
	@echo "Running unit tests"
	@python -m unittest discover -s tests -p "*_test.py"

subscribe:
	@echo "Subscribing to the topic"
	@./example_sub.sh