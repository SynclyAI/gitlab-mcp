import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


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
    server_base_url: str
    ssl_cert_path: Path
    ssl_key_path: Path

    @property
    def server_host(self) -> str:
        return urlparse(self.server_base_url).hostname

    @property
    def server_port(self) -> int:
        return urlparse(self.server_base_url).port

    @staticmethod
    def from_env() -> 'Config':
        url = os.environ.get('GITLAB_URL')
        if not url:
            raise ValueError('GITLAB_URL environment variable is required')

        secrets_path = Path(os.environ.get('GITLAB_SECRETS_PATH'))
        if not secrets_path.exists():
            raise ValueError(f'Secrets file not found: {secrets_path}')

        secrets = Secrets.from_file(secrets_path)

        server_base_url = os.environ.get('MCP_SERVER_BASE_URL')
        if not server_base_url:
            raise ValueError('MCP_SERVER_BASE_URL environment variable is required')

        parsed_url = urlparse(server_base_url)
        if parsed_url.scheme != 'https':
            raise ValueError('MCP_SERVER_BASE_URL must use https scheme')
        if not parsed_url.port:
            raise ValueError('MCP_SERVER_BASE_URL must include explicit port number')

        ssl_cert_env = os.environ.get('MCP_SSL_CERT_PATH')
        if not ssl_cert_env:
            raise ValueError('MCP_SSL_CERT_PATH environment variable is required')
        ssl_cert_path = Path(ssl_cert_env)
        if not ssl_cert_path.exists():
            raise ValueError(f'SSL certificate file not found: {ssl_cert_path}')

        ssl_key_env = os.environ.get('MCP_SSL_KEY_PATH')
        if not ssl_key_env:
            raise ValueError('MCP_SSL_KEY_PATH environment variable is required')
        ssl_key_path = Path(ssl_key_env)
        if not ssl_key_path.exists():
            raise ValueError(f'SSL key file not found: {ssl_key_path}')

        return Config(
            url=url,
            secrets=secrets,
            server_base_url=server_base_url,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
        )
