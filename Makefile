PYTHON := venv/bin/python
IMAGE := ghcr.io/synclyai/gitlab-mcp
VERSION := $(shell grep -Po '(?<=^version = ")[^"]*' pyproject.toml)

.PHONY: wheel image

wheel:
	rm -rf dist
	$(PYTHON) -m build --wheel

image: wheel
	docker build -f Dockerfile -t $(IMAGE):$(VERSION) dist/
