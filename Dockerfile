FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY gitlab_mcp/ gitlab_mcp/

RUN pip install --no-cache-dir .

ENTRYPOINT ["gitlab-mcp"]
