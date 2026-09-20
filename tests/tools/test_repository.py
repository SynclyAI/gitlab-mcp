from unittest.mock import MagicMock, patch

import pytest
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
    assert result.total_lines == 1
    assert result.start_line == 1


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


PROJECT_FILTERS = [
    ('search', 'needle'),
    ('owned', True),
    ('membership', True),
]

COMMIT_FILTERS = [
    ('ref_name', 'main'),
    ('since', '2024-01-01T00:00:00Z'),
    ('until', '2024-02-01T00:00:00Z'),
]


@pytest.mark.parametrize('name,value', PROJECT_FILTERS)
@patch('gitlab_mcp.tools.repository.get_client')
def test_list_projects_forwards_filter(mock_get_client, mock_client, name, value):
    mcp = FastMCP('test')
    mock_get_client.return_value.list_projects.return_value = []

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_projects')
    tool.fn(**{name: value})

    assert mock_get_client.return_value.list_projects.call_args.kwargs[name] == value


@pytest.mark.parametrize('name,value', COMMIT_FILTERS)
@patch('gitlab_mcp.tools.repository.get_client')
def test_list_commits_forwards_filter(mock_get_client, mock_client, name, value):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.commits.list.return_value = []
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_commits')
    tool.fn(project_id='1', **{name: value})

    assert mock_project.commits.list.call_args.kwargs[name] == value


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_repository_tree_forwards_path_and_ref(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.repository_tree.return_value = []
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_repository_tree')
    tool.fn(project_id='1', path='src', ref='main')

    params = mock_project.repository_tree.call_args.kwargs
    assert params['path'] == 'src'
    assert params['ref'] == 'main'


@patch('gitlab_mcp.tools.repository.get_client')
def test_search_code_forwards_ref(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.search.return_value = []
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'search_code')
    tool.fn(project_id='1', query='needle', ref='main')

    assert mock_project.search.call_args.kwargs['ref'] == 'main'


@patch('gitlab_mcp.tools.repository.get_client')
def test_list_branches_forwards_search(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.branches.list.return_value = []
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_branches')
    tool.fn(project_id='1', search='feature')

    assert mock_project.branches.list.call_args.kwargs['search'] == 'feature'


FILE_LINES = '\n'.join(f'line {n}' for n in range(1, 9)) + '\n'


def file_mock(content=FILE_LINES, file_path='src/Main.java'):
    file = MagicMock()
    file.file_path = file_path
    file.file_name = file_path.split('/')[-1]
    file.size = len(content)
    file.encoding = 'base64'
    file.decode.return_value = content.encode('utf-8')
    file.ref = 'main'
    file.last_commit_id = 'abc123'

    return file


def read_file(mock_get_client, mock_client, file=None, **kwargs):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.files.get.return_value = file if file is not None else file_mock()
    mock_get_client.return_value.get_project.return_value = mock_project

    repository.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_file_content')

    return tool.fn(project_id='1', file_path='src/Main.java', **kwargs)


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_whole_file_keeps_trailing_newline(mock_get_client, mock_client):
    result = read_file(mock_get_client, mock_client)

    assert result.content == FILE_LINES
    assert result.total_lines == 8
    assert result.start_line == 1


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_from_start_line(mock_get_client, mock_client):
    result = read_file(mock_get_client, mock_client, start_line=6)

    assert result.content == 'line 6\nline 7\nline 8'
    assert result.start_line == 6
    assert result.total_lines == 8


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_first_lines(mock_get_client, mock_client):
    result = read_file(mock_get_client, mock_client, line_count=2)

    assert result.content == 'line 1\nline 2'
    assert result.start_line == 1


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_exact_span(mock_get_client, mock_client):
    result = read_file(mock_get_client, mock_client, start_line=3, line_count=2)

    assert result.content == 'line 3\nline 4'
    assert result.start_line == 3


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_line_count_past_end_returns_remainder(mock_get_client, mock_client):
    result = read_file(mock_get_client, mock_client, start_line=7, line_count=10)

    assert result.content == 'line 7\nline 8'
    assert result.total_lines == 8


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_start_line_past_end(mock_get_client, mock_client):
    with pytest.raises(ValueError, match='File has 8 lines, start_line 9 is past the end'):
        read_file(mock_get_client, mock_client, start_line=9)


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_rejects_zero_start_line(mock_get_client, mock_client):
    with pytest.raises(ValueError, match='start_line must be 1 or greater'):
        read_file(mock_get_client, mock_client, start_line=0)


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_rejects_zero_line_count(mock_get_client, mock_client):
    with pytest.raises(ValueError, match='line_count must be 1 or greater'):
        read_file(mock_get_client, mock_client, line_count=0)


@patch('gitlab_mcp.tools.repository.get_client')
def test_get_file_content_rejects_binary_file(mock_get_client, mock_client):
    binary = file_mock(file_path='assets/logo.png')
    binary.decode.return_value = b'\x89PNG\r\n\x1a\n\xff\xfe'

    with pytest.raises(ValueError, match='assets/logo.png is not UTF-8 text'):
        read_file(mock_get_client, mock_client, file=binary)
