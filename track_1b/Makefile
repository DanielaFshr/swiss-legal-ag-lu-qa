.PHONY: run run-local infer
run:
	docker build -t swiss-legal-qa .
	docker run --rm swiss-legal-qa
run-local:
	python3 src/reproduce.py
infer:
	python3 src/inference.py
