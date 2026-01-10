from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from gitlab_mcp.tools import repository

GITLAB_URL = 'https://gitlab.example.com'


@patch('gitlab_mcp.tools.repository.get_client')
def test_list_projects(mock_get_client, mock_client, mock_project):
    mcp = FastMCP('test')
    mock_get_client.return_value.list_projects.return_value = [mock_project]

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_projects')
    result = tool.fn()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].name == 'test-project'


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_repository_tree(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.repository_tree.return_value = [
        {'id': 'abc123', 'name': 'README.md', 'type': 'blob', 'path': 'README.md', 'mode': '100644'},
    ]
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_repository_tree')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0].name == 'README.md'
    assert result[0].type == 'blob'
    mock_get_client.assert_called_once()


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content(mock_get_client, mock_client):
    mcp = FastMCP('test')
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
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_file_content')
    result = tool.fn(project_id='1', file_path='README.md')

    assert result.file_path == 'README.md'
    assert result.content == '# Test'


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_blame(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.files.blame.return_value = [
        {
            'commit': {
                'id': 'abc123',
                'author_name': 'Test User',
                'author_email': 'test@example.com',
                'message': 'Initial commit',
                'committed_date': '2024-01-01T00:00:00Z',
            },
            'lines': ['line1', 'line2'],
        }
    ]
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_file_blame')
    result = tool.fn(project_id='1', file_path='README.md')

    assert len(result) == 1
    assert result[0].commit.id == 'abc123'
    assert result[0].lines == ['line1', 'line2']


@patch('gitlab_mcp.tools.repository.get_client')
def test_search_code(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.search.return_value = [
        {
            'basename': 'test',
            'data': 'def test():',
            'path': 'src/test.py',
            'filename': 'test.py',
            'ref': 'main',
            'startline': 1,
            'project_id': 1,
        }
    ]
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'search_code')
    result = tool.fn(project_id='1', query='def test')

    assert len(result) == 1
    assert result[0].path == 'src/test.py'
    assert result[0].data == 'def test():'


@patch('gitlab_mcp.tools.repository.get_client')
def test_list_branches(mock_get_client, mock_client):
    mcp = FastMCP('test')
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
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_branches')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0].name == 'main'
    assert result[0].default is True


@patch('gitlab_mcp.tools.repository.get_client')
def test_list_commits(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_commit = MagicMock()
    mock_commit.id = 'abc123'
    mock_commit.short_id = 'abc123'
    mock_commit.title = 'Test commit'
    mock_commit.message = 'Test commit message'
    mock_commit.author_name = 'Test User'
    mock_commit.author_email = 'test@example.com'
    mock_commit.authored_date = '2024-01-01T00:00:00Z'
    mock_commit.committer_name = 'Test User'
    mock_commit.committed_date = '2024-01-01T00:00:00Z'
    mock_commit.web_url = 'https://gitlab.example.com/group/test-project/-/commit/abc123'
    mock_project.commits.list.return_value = [mock_commit]
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_commits')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0].id == 'abc123'
    assert result[0].title == 'Test commit'


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_commit(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_commit = MagicMock()
    mock_commit.id = 'abc123'
    mock_commit.short_id = 'abc123'
    mock_commit.title = 'Test commit'
    mock_commit.message = 'Test commit message'
    mock_commit.author_name = 'Test User'
    mock_commit.author_email = 'test@example.com'
    mock_commit.authored_date = '2024-01-01T00:00:00Z'
    mock_commit.committer_name = 'Test User'
    mock_commit.committed_date = '2024-01-01T00:00:00Z'
    mock_commit.web_url = 'https://gitlab.example.com/group/test-project/-/commit/abc123'
    mock_commit.parent_ids = ['parent123']
    mock_commit.stats = {'additions': 10, 'deletions': 5, 'total': 15}
    mock_project.commits.get.return_value = mock_commit
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_commit')
    result = tool.fn(project_id='1', sha='abc123')

    assert result.id == 'abc123'
    assert result.stats['additions'] == 10
    assert result.parent_ids == ['parent123']
