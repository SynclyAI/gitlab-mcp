import json
import pytest
from pathlib import Path
from unittest.mock import patch

from gitlab_mcp.config import Config, Secrets


def test_secrets_from_file(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    secrets = Secrets.from_file(secrets_file)

    assert secrets.oauth_client_id == 'test-client-id'
    assert secrets.oauth_client_secret == 'test-client-secret'
    assert secrets.service_token == 'test-service-token'


def test_secrets_from_file_missing_field(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
    }))

    with pytest.raises(KeyError):
        Secrets.from_file(secrets_file)


def test_config_from_env_missing_gitlab_url(tmp_path):
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match='GITLAB_URL environment variable is required'):
            Config.from_env()


def test_config_from_env_missing_bind_url(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
    }, clear=True):
        with pytest.raises(ValueError, match='MCP_SERVER_BIND_URL environment variable is required'):
            Config.from_env()


def test_config_from_env_missing_advertised_url(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'http://0.0.0.0:8080',
    }, clear=True):
        with pytest.raises(ValueError, match='MCP_SERVER_ADVERTISED_URL environment variable is required'):
            Config.from_env()


def test_config_from_env_invalid_scheme(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'ftp://localhost:8443',
    }, clear=True):
        with pytest.raises(ValueError, match='MCP_SERVER_BIND_URL must use http or https scheme'):
            Config.from_env()


def test_config_from_env_missing_port(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'https://localhost',
    }, clear=True):
        with pytest.raises(ValueError, match='MCP_SERVER_BIND_URL must include explicit port number'):
            Config.from_env()


def test_config_from_env_missing_ssl_cert_when_https_bind(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'https://localhost:8443',
        'MCP_SERVER_ADVERTISED_URL': 'https://mcp.example.com:8443',
    }, clear=True):
        with pytest.raises(ValueError, match='MCP_SSL_CERT_PATH environment variable is required'):
            Config.from_env()


def test_config_from_env_missing_ssl_key_when_https_bind(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))
    ssl_cert = tmp_path / 'cert.pem'
    ssl_cert.write_text('cert')

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'https://localhost:8443',
        'MCP_SERVER_ADVERTISED_URL': 'https://mcp.example.com:8443',
        'MCP_SSL_CERT_PATH': str(ssl_cert),
    }, clear=True):
        with pytest.raises(ValueError, match='MCP_SSL_KEY_PATH environment variable is required'):
            Config.from_env()


def test_config_from_env_success_with_https_bind(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))
    ssl_cert = tmp_path / 'cert.pem'
    ssl_cert.write_text('cert')
    ssl_key = tmp_path / 'key.pem'
    ssl_key.write_text('key')

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'https://localhost:8443',
        'MCP_SERVER_ADVERTISED_URL': 'https://mcp.example.com:8443',
        'MCP_SSL_CERT_PATH': str(ssl_cert),
        'MCP_SSL_KEY_PATH': str(ssl_key),
    }, clear=True):
        config = Config.from_env()

        assert config.url == 'https://gitlab.example.com'
        assert config.server_bind_url == 'https://localhost:8443'
        assert config.server_advertised_url == 'https://mcp.example.com:8443'
        assert config.ssl_cert_path == ssl_cert
        assert config.ssl_key_path == ssl_key
        assert config.bind_uses_tls is True


def test_config_from_env_success_with_http_bind(tmp_path):
    secrets_file = tmp_path / 'secrets.json'
    secrets_file.write_text(json.dumps({
        'oauth_client_id': 'test-client-id',
        'oauth_client_secret': 'test-client-secret',
        'service_token': 'test-service-token',
    }))

    with patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_SECRETS_PATH': str(secrets_file),
        'MCP_SERVER_BIND_URL': 'http://0.0.0.0:8080',
        'MCP_SERVER_ADVERTISED_URL': 'https://mcp.example.com:443',
    }, clear=True):
        config = Config.from_env()

        assert config.server_bind_url == 'http://0.0.0.0:8080'
        assert config.server_advertised_url == 'https://mcp.example.com:443'
        assert config.ssl_cert_path is None
        assert config.ssl_key_path is None
        assert config.bind_uses_tls is False


def test_config_server_host():
    config = Config(
        url='https://gitlab.example.com',
        secrets=Secrets('id', 'secret', 'token'),
        server_bind_url='https://mcp.example.com:8443',
        server_advertised_url='https://mcp.public.com:8443',
        ssl_cert_path=Path('/cert.pem'),
        ssl_key_path=Path('/key.pem'),
    )

    assert config.server_host == 'mcp.example.com'


def test_config_server_port():
    config = Config(
        url='https://gitlab.example.com',
        secrets=Secrets('id', 'secret', 'token'),
        server_bind_url='https://mcp.example.com:8443',
        server_advertised_url='https://mcp.public.com:8443',
        ssl_cert_path=Path('/cert.pem'),
        ssl_key_path=Path('/key.pem'),
    )

    assert config.server_port == 8443
