from fastmcp import FastMCP

from gitlab_mcp.config import Config
from gitlab_mcp.client import GitLabClient

mcp = FastMCP('GitLab MCP')

config: Config | None = None
service_client: GitLabClient | None = None


def get_service_client() -> GitLabClient:
    global service_client, config
    if service_client is None:
        config = Config.from_env()
        service_client = GitLabClient(
            url=config.url,
            token=config.secrets.service_token,
            ca_cert_path=config.ca_cert_path,
        )

    return service_client


def main():
    from gitlab_mcp.tools import merge_requests, repository
    merge_requests.register_tools(mcp, get_service_client)
    repository.register_tools(mcp, get_service_client)
    mcp.run()


if __name__ == '__main__':
    main()
