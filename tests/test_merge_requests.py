from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from gitlab_mcp.tools import merge_requests

GITLAB_URL = 'https://gitlab.example.com'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_list_merge_requests(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.list.return_value = [mock_merge_request]
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'list_merge_requests')
    result = tool.fn(project_id='1')

    assert len(result) == 1
    assert result[0]['iid'] == 1
    assert result[0]['title'] == 'Test MR'
    assert result[0]['state'] == 'opened'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    assert result['iid'] == 1
    assert result['title'] == 'Test MR'
    assert result['description'] == 'Test description'


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

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_changes')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result['changes']) == 1
    assert result['changes'][0]['old_path'] == 'file.py'
    assert '@@ -1 +1 @@' in result['changes'][0]['diff']


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

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'add_merge_request_comment')
    result = tool.fn(project_id='1', mr_iid=1, body='Test comment')

    assert result['id'] == 1
    assert result['body'] == 'Test comment'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_approve_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL, None)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'approve_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    mock_merge_request.approve.assert_called_once()
    assert result['status'] == 'approved'
    assert result['mr_iid'] == 1
