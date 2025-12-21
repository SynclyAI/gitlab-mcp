from fastmcp.server.auth import OAuthProxy

from gitlab_mcp.config import Config
from gitlab_mcp.client import GitLabClient


class PermissionDenied(Exception):
    pass


def create_oauth_proxy(config: Config) -> OAuthProxy:
    gitlab_url = config.url.rstrip('/')

    return OAuthProxy(
        upstream_authorization_endpoint=f'{gitlab_url}/oauth/authorize',
        upstream_token_endpoint=f'{gitlab_url}/oauth/token',
        upstream_client_id=config.secrets.oauth_client_id,
        upstream_client_secret=config.secrets.oauth_client_secret,
        base_url='http://localhost:8000',
        redirect_path='callback',
        scopes=['read_user', 'read_api', 'read_repository'],
    )


def check_project_access(
    project_id: str | int,
    user_token: str,
    config: Config,
) -> None:
    user_client = GitLabClient(
        url=config.url,
        token=user_token,
        ca_cert_path=config.ca_cert_path,
    )
    try:
        user_client.get_project(project_id)
    except Exception:
        raise PermissionDenied(f'User cannot access project {project_id}')

    service_client = GitLabClient(
        url=config.url,
        token=config.secrets.service_token,
        ca_cert_path=config.ca_cert_path,
    )
    try:
        service_client.get_project(project_id)
    except Exception:
        raise PermissionDenied(f'AI not enabled for project {project_id}')
