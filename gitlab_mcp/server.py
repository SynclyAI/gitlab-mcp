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
    ca_cert_path=config.ca_cert_path,
)


def get_config() -> Config:
    return config


def main():
    merge_requests.register_tools(mcp, service_client, config.url, config.ca_cert_path)
    repository.register_tools(mcp, service_client, config.url, config.ca_cert_path)
    mcp.run()


if __name__ == '__main__':
    main()
