from unittest.mock import MagicMock, patch

from gitlab_mcp.auth import create_oauth_proxy

GITLAB_URL = 'https://gitlab.example.com'


def config_mock(url=GITLAB_URL):
    config = MagicMock()
    config.url = url
    config.secrets.oauth_client_id = 'client-id'
    config.secrets.oauth_client_secret = 'client-secret'
    config.server_advertised_url = 'https://mcp.example.com'

    return config


@patch('gitlab_mcp.auth.OAuthProxy')
@patch('gitlab_mcp.auth.IntrospectionTokenVerifier')
def test_create_oauth_proxy_points_at_gitlab_endpoints(mock_verifier, mock_proxy):
    create_oauth_proxy(config_mock())

    assert mock_verifier.call_args.kwargs['introspection_url'] == f'{GITLAB_URL}/oauth/introspect'
    kwargs = mock_proxy.call_args.kwargs
    assert kwargs['upstream_authorization_endpoint'] == f'{GITLAB_URL}/oauth/authorize'
    assert kwargs['upstream_token_endpoint'] == f'{GITLAB_URL}/oauth/token'
    assert kwargs['base_url'] == 'https://mcp.example.com'


@patch('gitlab_mcp.auth.OAuthProxy')
@patch('gitlab_mcp.auth.IntrospectionTokenVerifier')
def test_create_oauth_proxy_strips_trailing_slash(mock_verifier, mock_proxy):
    create_oauth_proxy(config_mock(url=f'{GITLAB_URL}/'))

    assert mock_verifier.call_args.kwargs['introspection_url'] == f'{GITLAB_URL}/oauth/introspect'
    assert mock_proxy.call_args.kwargs['upstream_token_endpoint'] == f'{GITLAB_URL}/oauth/token'


@patch('gitlab_mcp.auth.OAuthProxy')
@patch('gitlab_mcp.auth.IntrospectionTokenVerifier')
def test_create_oauth_proxy_passes_credentials_and_scopes(mock_verifier, mock_proxy):
    create_oauth_proxy(config_mock())

    assert mock_verifier.call_args.kwargs['required_scopes'] == ['read_user', 'api', 'read_repository']
    assert mock_verifier.call_args.kwargs['client_id'] == 'client-id'
    kwargs = mock_proxy.call_args.kwargs
    assert kwargs['upstream_client_id'] == 'client-id'
    assert kwargs['upstream_client_secret'] == 'client-secret'
