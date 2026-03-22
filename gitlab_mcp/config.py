import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Secrets:
    oauth_client_id: str
    oauth_client_secret: str
    service_token: str

    @staticmethod
    def from_file(path: Path) -> 'Secrets':
        with open(path) as f:
            data = json.load(f)

        return Secrets(
            oauth_client_id=data['oauth_client_id'],
            oauth_client_secret=data['oauth_client_secret'],
            service_token=data['service_token'],
        )


@dataclass(frozen=True)
class Config:
    url: str
    secrets: Secrets
    server_bind_url: str
    server_advertised_url: str
    ssl_cert_path: Optional[Path]
    ssl_key_path: Optional[Path]

    @property
    def server_host(self) -> str:
        return urlparse(self.server_bind_url).hostname

    @property
    def server_port(self) -> int:
        return urlparse(self.server_bind_url).port

    @property
    def bind_uses_tls(self) -> bool:
        return urlparse(self.server_bind_url).scheme == 'https'

    @staticmethod
    def _validate_url(value: str, name: str) -> None:
        parsed = urlparse(value)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f'{name} must use http or https scheme')
        if not parsed.port:
            raise ValueError(f'{name} must include explicit port number')

    @staticmethod
    def from_env() -> 'Config':
        url = os.environ.get('GITLAB_URL')
        if not url:
            raise ValueError('GITLAB_URL environment variable is required')

        secrets_path = Path(os.environ.get('GITLAB_SECRETS_PATH'))
        if not secrets_path.exists():
            raise ValueError(f'Secrets file not found: {secrets_path}')

        secrets = Secrets.from_file(secrets_path)

        server_bind_url = os.environ.get('MCP_SERVER_BIND_URL')
        if not server_bind_url:
            raise ValueError('MCP_SERVER_BIND_URL environment variable is required')
        Config._validate_url(server_bind_url, 'MCP_SERVER_BIND_URL')

        server_advertised_url = os.environ.get('MCP_SERVER_ADVERTISED_URL')
        if not server_advertised_url:
            raise ValueError('MCP_SERVER_ADVERTISED_URL environment variable is required')
        Config._validate_url(server_advertised_url, 'MCP_SERVER_ADVERTISED_URL')

        if urlparse(server_advertised_url).scheme == 'http':
            logger.warning('MCP_SERVER_ADVERTISED_URL uses http - clients will connect without TLS')

        bind_uses_tls = urlparse(server_bind_url).scheme == 'https'
        ssl_cert_path = None
        ssl_key_path = None

        if bind_uses_tls:
            ssl_cert_env = os.environ.get('MCP_SSL_CERT_PATH')
            if not ssl_cert_env:
                raise ValueError('MCP_SSL_CERT_PATH environment variable is required when bind URL uses https')
            ssl_cert_path = Path(ssl_cert_env)
            if not ssl_cert_path.exists():
                raise ValueError(f'SSL certificate file not found: {ssl_cert_path}')

            ssl_key_env = os.environ.get('MCP_SSL_KEY_PATH')
            if not ssl_key_env:
                raise ValueError('MCP_SSL_KEY_PATH environment variable is required when bind URL uses https')
            ssl_key_path = Path(ssl_key_env)
            if not ssl_key_path.exists():
                raise ValueError(f'SSL key file not found: {ssl_key_path}')

        return Config(
            url=url,
            secrets=secrets,
            server_bind_url=server_bind_url,
            server_advertised_url=server_advertised_url,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
        )
