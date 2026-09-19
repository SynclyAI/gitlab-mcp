FROM python:3.11-slim

WORKDIR /app

COPY gitlab_mcp-*.whl /tmp/

RUN pip install --no-cache-dir /tmp/gitlab_mcp-*.whl && rm /tmp/*.whl

ENTRYPOINT ["gitlab-mcp"]
