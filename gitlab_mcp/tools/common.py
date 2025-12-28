from pathlib import Path

from fastmcp.server.dependencies import get_access_token

from gitlab_mcp.client import CompositeGitLabClient, TokenGitLabClient


def get_client(
    service_client: TokenGitLabClient,
    url: str,
    ca_cert_path: Path | None,
) -> CompositeGitLabClient:
    token = get_access_token()

    return CompositeGitLabClient(token.token, service_client, url, ca_cert_path)
