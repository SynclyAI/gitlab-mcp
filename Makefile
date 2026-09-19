PYTHON := venv/bin/python
VERSION := $(shell grep -Po '(?<=^version = ")[^"]*' pyproject.toml)

.PHONY: wheel image

wheel:
	rm -rf dist
	$(PYTHON) -m build --wheel

image: wheel
	docker build -f Dockerfile -t gitlab-mcp:$(VERSION) dist/
