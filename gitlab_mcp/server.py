from fastmcp import FastMCP

from gitlab_mcp.auth import create_oauth_proxy
from gitlab_mcp.config import Config
from gitlab_mcp.client import GitLabClient
from gitlab_mcp.tools import merge_requests, repository

config = Config.from_env()
auth = create_oauth_proxy(config)
mcp = FastMCP('GitLab MCP', auth=auth)

service_client: GitLabClient | None = None


def get_service_client() -> GitLabClient:
    global service_client
    if service_client is None:
        service_client = GitLabClient(
            url=config.url,
            token=config.secrets.service_token,
            ca_cert_path=config.ca_cert_path,
        )

    return service_client


def get_config() -> Config:
    return config


def main():
    merge_requests.register_tools(mcp, get_service_client)
    repository.register_tools(mcp, get_service_client)
    mcp.run()


if __name__ == '__main__':
    main()
