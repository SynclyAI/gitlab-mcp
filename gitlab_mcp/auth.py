from fastmcp.server.auth import OAuthProxy
from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

from gitlab_mcp.config import Config


def create_oauth_proxy(config: Config) -> OAuthProxy:
    gitlab_url = config.url.rstrip('/')

    token_verifier = IntrospectionTokenVerifier(
        introspection_url=f'{gitlab_url}/oauth/introspect',
        client_id=config.secrets.oauth_client_id,
        client_secret=config.secrets.oauth_client_secret,
        required_scopes=['read_user', 'api', 'read_repository'],
    )

    return OAuthProxy(
        upstream_authorization_endpoint=f'{gitlab_url}/oauth/authorize',
        upstream_token_endpoint=f'{gitlab_url}/oauth/token',
        upstream_client_id=config.secrets.oauth_client_id,
        upstream_client_secret=config.secrets.oauth_client_secret,
        token_verifier=token_verifier,
        base_url=config.server_base_url,
        redirect_path='callback',
        token_endpoint_auth_method='client_secret_post',
    )
