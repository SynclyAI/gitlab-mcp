from fastmcp import FastMCP

from gitlab_mcp.auth import create_oauth_proxy
from gitlab_mcp.config import Config
from gitlab_mcp.client import TokenGitLabClient
from gitlab_mcp.tools import merge_requests, repository

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
        },
    )


if __name__ == '__main__':
    main()
