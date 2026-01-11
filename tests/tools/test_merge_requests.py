from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from gitlab_mcp.tools import merge_requests

GITLAB_URL = 'https://gitlab.example.com'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_search_merge_requests(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_get_client.return_value.list_merge_requests.return_value = [mock_merge_request]

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'search_merge_requests')
    result = tool.fn(state='opened', scope='all')

    assert len(result) == 1
    assert result[0].iid == 1
    assert result[0].title == 'Test MR'
    mock_get_client.return_value.list_merge_requests.assert_called_once_with(
        iterator=True, state='opened', scope='all'
    )


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_list_merge_requests(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.list.return_value = [mock_merge_request]
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_merge_requests')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0].iid == 1
    assert result[0].title == 'Test MR'
    assert result[0].state == 'opened'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    assert result.iid == 1
    assert result.title == 'Test MR'
    assert result.description == 'Test description'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request_changes(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.changes.return_value = {
        'changes': [
            {
                'old_path': 'file.py',
                'new_path': 'file.py',
                'a_mode': '100644',
                'b_mode': '100644',
                'new_file': False,
                'renamed_file': False,
                'deleted_file': False,
                'diff': '@@ -1 +1 @@\n-old\n+new',
            }
        ]
    }
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_changes')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result.changes) == 1
    assert result.changes[0].old_path == 'file.py'
    assert '@@ -1 +1 @@' in result.changes[0].diff


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_mr_commits(mock_get_client, mock_client, mock_merge_request):
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
    mock_commit.committed_date = '2024-01-01T00:00:00Z'
    mock_merge_request.commits.return_value = [mock_commit]
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_mr_commits')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result) == 1
    assert result[0].id == 'abc123'
    assert result[0].title == 'Test commit'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_mr_pipelines(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.pipelines.return_value = [
        {
            'id': 123,
            'sha': 'abc123',
            'ref': 'feature',
            'status': 'success',
            'web_url': 'https://gitlab.example.com/group/test-project/-/pipelines/123',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
        }
    ]
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_mr_pipelines')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result) == 1
    assert result[0].id == 123
    assert result[0].status == 'success'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_mr_discussions(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_discussion = MagicMock()
    mock_discussion.id = 'disc123'
    mock_discussion.individual_note = False
    mock_discussion.attributes = {
        'notes': [
            {
                'id': 1,
                'body': 'Test note',
                'author': {'username': 'testuser'},
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z',
                'system': False,
                'resolvable': True,
                'resolved': False,
                'position': None,
            }
        ]
    }
    mock_merge_request.discussions.list.return_value = [mock_discussion]
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_mr_discussions')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result) == 1
    assert result[0].id == 'disc123'
    assert len(result[0].notes) == 1
    assert result[0].notes[0].body == 'Test note'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_add_mr_discussion(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_discussion = MagicMock()
    mock_discussion.id = 'disc123'
    mock_discussion.attributes = {
        'notes': [
            {
                'id': 1,
                'body': 'New discussion',
                'author': {'username': 'testuser'},
                'created_at': '2024-01-01T00:00:00Z',
            }
        ]
    }
    mock_merge_request.discussions.create.return_value = mock_discussion
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'add_mr_discussion')
    result = tool.fn(project_id='1', mr_iid=1, body='New discussion')

    assert result.id == 'disc123'
    assert len(result.notes) == 1


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_add_merge_request_comment(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_note = MagicMock()
    mock_note.id = 1
    mock_note.body = 'Test comment'
    mock_note.author = {'username': 'testuser'}
    mock_note.created_at = '2024-01-01T00:00:00Z'
    mock_merge_request.notes.create.return_value = mock_note
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'add_merge_request_comment')
    result = tool.fn(project_id='1', mr_iid=1, body='Test comment')

    assert result.id == 1
    assert result.body == 'Test comment'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.create.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request')
    result = tool.fn(
        project_id='1',
        source_branch='feature',
        target_branch='main',
        title='Test MR',
    )

    assert result.iid == 1
    assert result.title == 'Test MR'
    mock_project.mergerequests.create.assert_called_once()


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_approve_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'approve_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    mock_merge_request.approve.assert_called_once()
    assert result.status == 'approved'
    assert result.mr_iid == 1


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_unapprove_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'unapprove_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    mock_merge_request.unapprove.assert_called_once()
    assert result.status == 'unapproved'
    assert result.mr_iid == 1


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_merge_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'merge_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    mock_merge_request.merge.assert_called_once()
    assert result.status == 'merged'
    assert result.mr_iid == 1
