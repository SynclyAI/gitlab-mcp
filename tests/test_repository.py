from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from gitlab_mcp.tools import repository

GITLAB_URL = 'https://gitlab.example.com'


def test_list_projects(mock_client, mock_project):
    mcp = FastMCP('test')
    mock_client.list_projects.return_value = [mock_project]

    repository.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_projects')
    result = tool.fn()

    assert len(result) == 1
    assert result[0]['id'] == 1
    assert result[0]['name'] == 'test-project'


@patch('gitlab_mcp.tools.repository.CompositeGitLabClient')
@patch('gitlab_mcp.tools.repository.get_access_token')
def test_get_repository_tree(mock_get_token, mock_composite_client, mock_client):
    mcp = FastMCP('test')
    mock_get_token.return_value = MagicMock(token='user_token')
    mock_project = MagicMock()
    mock_project.repository_tree.return_value = [
        {'id': 'abc123', 'name': 'README.md', 'type': 'blob', 'path': 'README.md', 'mode': '100644'},
    ]
    mock_composite_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_repository_tree')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0]['name'] == 'README.md'
    assert result[0]['type'] == 'blob'
    mock_composite_client.assert_called_once()


@patch('gitlab_mcp.tools.repository.CompositeGitLabClient')
@patch('gitlab_mcp.tools.repository.get_access_token')
def test_get_file_content(mock_get_token, mock_composite_client, mock_client):
    mcp = FastMCP('test')
    mock_get_token.return_value = MagicMock(token='user_token')
    mock_project = MagicMock()
    mock_file = MagicMock()
    mock_file.file_path = 'README.md'
    mock_file.file_name = 'README.md'
    mock_file.size = 100
    mock_file.encoding = 'base64'
    mock_file.decode.return_value = b'# Test'
    mock_file.ref = 'main'
    mock_file.last_commit_id = 'abc123'
    mock_project.files.get.return_value = mock_file
    mock_composite_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_file_content')
    result = tool.fn(project_id='1', file_path='README.md')

    assert result['file_path'] == 'README.md'
    assert result['content'] == '# Test'


@patch('gitlab_mcp.tools.repository.CompositeGitLabClient')
@patch('gitlab_mcp.tools.repository.get_access_token')
def test_list_branches(mock_get_token, mock_composite_client, mock_client):
    mcp = FastMCP('test')
    mock_get_token.return_value = MagicMock(token='user_token')
    mock_project = MagicMock()
    mock_branch = MagicMock()
    mock_branch.name = 'main'
    mock_branch.merged = False
    mock_branch.protected = True
    mock_branch.default = True
    mock_branch.web_url = 'https://gitlab.example.com/group/test-project/-/tree/main'
    mock_branch.commit = {
        'id': 'abc123',
        'short_id': 'abc123',
        'title': 'Initial commit',
        'author_name': 'Test',
        'committed_date': '2024-01-01T00:00:00Z',
    }
    mock_project.branches.list.return_value = [mock_branch]
    mock_composite_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_branches')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0]['name'] == 'main'
    assert result[0]['default'] is True
