import httpx

from fastmcp.server.auth import AccessToken, OAuthProxy, TokenVerifier

from gitlab_mcp.config import Config


class GitLabTokenVerifier(TokenVerifier):
    def __init__(
        self,
        introspection_endpoint: str,
        client_id: str,
        client_secret: str,
        required_scopes: list[str],
    ):
        self._introspection_endpoint = introspection_endpoint
        self._client_id = client_id
        self._client_secret = client_secret
        self._required_scopes = required_scopes

    @property
    def required_scopes(self) -> list[str]:
        return self._required_scopes

    def verify_token(self, token: str) -> AccessToken | None:
        response = httpx.post(
            self._introspection_endpoint,
            data={'token': token},
            auth=(self._client_id, self._client_secret),
        )
        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get('active', False):
            return None

        token_scopes = set(data.get('scope', '').split())
        if not set(self._required_scopes).issubset(token_scopes):
            return None

        return AccessToken(
            token=token,
            client_id=data.get('client_id', ''),
            scopes=list(token_scopes),
        )


def create_oauth_proxy(config: Config) -> OAuthProxy:
    gitlab_url = config.url.rstrip('/')

    token_verifier = GitLabTokenVerifier(
        introspection_endpoint=f'{gitlab_url}/oauth/introspect',
        client_id=config.secrets.oauth_client_id,
        client_secret=config.secrets.oauth_client_secret,
        required_scopes=['read_user', 'read_api', 'read_repository'],
    )

    return OAuthProxy(
        upstream_authorization_endpoint=f'{gitlab_url}/oauth/authorize',
        upstream_token_endpoint=f'{gitlab_url}/oauth/token',
        upstream_client_id=config.secrets.oauth_client_id,
        upstream_client_secret=config.secrets.oauth_client_secret,
        token_verifier=token_verifier,
        base_url=config.server_base_url,
        redirect_path='callback',
    )
