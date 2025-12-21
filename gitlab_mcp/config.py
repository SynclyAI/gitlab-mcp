import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Secrets:
    oauth_client_id: str
    oauth_client_secret: str
    service_token: str

    @classmethod
    def from_file(cls, path: Path) -> 'Secrets':
        with open(path) as f:
            data = json.load(f)

        return cls(
            oauth_client_id=data['oauth_client_id'],
            oauth_client_secret=data['oauth_client_secret'],
            service_token=data['service_token'],
        )


@dataclass(frozen=True)
class Config:
    url: str
    secrets: Secrets
    ca_cert_path: Path | None = None

    @classmethod
    def from_env(cls) -> 'Config':
        url = os.environ.get('GITLAB_URL')
        if not url:
            raise ValueError('GITLAB_URL environment variable is required')

        secrets_path = Path(os.environ.get('GITLAB_SECRETS_PATH', '/run/secrets/gitlab.json'))
        if not secrets_path.exists():
            raise ValueError(f'Secrets file not found: {secrets_path}')

        secrets = Secrets.from_file(secrets_path)

        ca_cert_path = None
        ca_cert_env = os.environ.get('GITLAB_CA_CERT_PATH')
        if ca_cert_env:
            ca_cert_path = Path(ca_cert_env)
            if not ca_cert_path.exists():
                raise ValueError(f'CA certificate file not found: {ca_cert_path}')

        return cls(url=url, secrets=secrets, ca_cert_path=ca_cert_path)
