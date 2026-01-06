from fastmcp import FastMCP

from gitlab_mcp.auth import create_oauth_proxy
from gitlab_mcp.config import Config
from gitlab_mcp.client import TokenGitLabClient
from gitlab_mcp.tools import merge_requests, repository

UVICORN_LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)-8s %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S',
        },
        'access': {
            'format': '[%(asctime)s] %(levelname)-8s %(client_addr)s - "%(request_line)s" %(status_code)s',
            'datefmt': '%y/%m/%d %H:%M:%S',
        },
    },
    'handlers': {
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
        'access': {
            'formatter': 'access',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        'uvicorn': {'handlers': ['default'], 'level': 'INFO', 'propagate': False},
        'uvicorn.error': {'level': 'INFO'},
        'uvicorn.access': {'handlers': ['access'], 'level': 'INFO', 'propagate': False},
    },
}

config = Config.from_env()
auth = create_oauth_proxy(config)
mcp = FastMCP('GitLab MCP', auth=auth)
service_client = TokenGitLabClient(
    url=config.url,
    token=config.secrets.service_token,
)


def get_config() -> Config:
    return config


def main():
    merge_requests.register_tools(mcp, service_client, config.url)
    repository.register_tools(mcp, service_client, config.url)
    mcp.run(
        transport='http',
        host=config.server_host,
        port=config.server_port,
        uvicorn_config={
            'ssl_certfile': str(config.ssl_cert_path),
            'ssl_keyfile': str(config.ssl_key_path),
            'log_config': UVICORN_LOG_CONFIG,
        },
    )


if __name__ == '__main__':
    main()
