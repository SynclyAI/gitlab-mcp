from fastmcp.server.dependencies import get_access_token

from gitlab_mcp.client import CompositeGitLabClient, OAuthGitLabClient, TokenGitLabClient


def get_client(
    service_client: TokenGitLabClient,
    url: str,
) -> CompositeGitLabClient:
    token = get_access_token()

    return CompositeGitLabClient(token.token, service_client, url)


def get_user_client(url: str) -> OAuthGitLabClient:
    token = get_access_token()

    return OAuthGitLabClient(url, token.token)
