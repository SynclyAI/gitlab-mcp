import asyncio
from unittest.mock import MagicMock, patch

import gitlab.exceptions
from fastmcp import Client, FastMCP

from gitlab_mcp.client import PermissionDenied, ProjectNotFound
from gitlab_mcp.tools import repository
from gitlab_mcp.tools.common import get_client

GITLAB_URL = 'https://gitlab.example.com'


def call_get_repository_tree(error):
    mcp = FastMCP('test')

    with patch('gitlab_mcp.tools.repository.get_client') as get_client:
        get_client.return_value.get_project.side_effect = error
        repository.register_tools(mcp, None, GITLAB_URL)

        async def call():
            async with Client(mcp) as client:
                return await client.call_tool('get_repository_tree', {'project_id': '1'}, raise_on_error=False)

        return asyncio.run(call())


def assert_reported(result, message):
    assert result.is_error is True
    assert result.content[0].text.endswith(message)


def test_project_not_found_reported_to_client():
    result = call_get_repository_tree(ProjectNotFound('Project 123 not found'))

    assert_reported(result, 'Project 123 not found')


def test_permission_denied_reported_to_client():
    result = call_get_repository_tree(PermissionDenied('Access denied'))

    assert_reported(result, 'Access denied')


def test_gitlab_error_reported_to_client():
    result = call_get_repository_tree(gitlab.exceptions.GitlabGetError('500: Internal Server Error'))

    assert_reported(result, '500: Internal Server Error')


@patch('gitlab_mcp.tools.common.CompositeGitLabClient')
@patch('gitlab_mcp.tools.common.get_access_token')
def test_get_client_passes_caller_token(mock_access_token, mock_composite):
    mock_access_token.return_value = MagicMock(token='caller-token')
    service_client = MagicMock()

    client = get_client(service_client, GITLAB_URL)

    mock_composite.assert_called_once_with('caller-token', service_client, GITLAB_URL)
    assert client is mock_composite.return_value
