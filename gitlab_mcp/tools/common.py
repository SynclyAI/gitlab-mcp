from functools import wraps

import gitlab.exceptions
from fastmcp.server.dependencies import get_access_token
from mcp.types import CallToolResult, TextContent

from gitlab_mcp.client import CompositeGitLabClient, PermissionDenied, ProjectNotFound, TokenGitLabClient


def get_client(
    service_client: TokenGitLabClient,
    url: str,
) -> CompositeGitLabClient:
    token = get_access_token()

    return CompositeGitLabClient(token.token, service_client, url)


def handle_gitlab_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ProjectNotFound, PermissionDenied, gitlab.exceptions.GitlabError) as e:
            return CallToolResult(
                content=[TextContent(type='text', text=str(e))],
                isError=True,
            )

    return wrapper
