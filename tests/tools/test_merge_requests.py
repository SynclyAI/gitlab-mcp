from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

from gitlab_mcp.client import UserNotFound
from gitlab_mcp.tools import merge_requests

GITLAB_URL = 'https://gitlab.example.com'


def discussion_with_note(body, discussion_id='disc123', resolved=False):
    discussion = MagicMock()
    discussion.id = discussion_id
    discussion.attributes = {
        'individual_note': False,
        'notes': [
            {
                'id': 1,
                'body': body,
                'author': {'username': 'testuser'},
                'created_at': '2024-01-01T00:00:00Z',
                'resolved': resolved,
            }
        ],
    }

    return discussion


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
        ],
        'diff_refs': {'base_sha': 'base1', 'start_sha': 'start1', 'head_sha': 'head1'},
    }
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_changes')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result.changes) == 1
    assert result.changes[0].old_path == 'file.py'
    assert '@@ -1 +1 @@' in result.changes[0].diff
    assert result.diff_refs.base_sha == 'base1'
    assert result.diff_refs.head_sha == 'head1'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request_commits(mock_get_client, mock_client, mock_merge_request):
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

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_commits')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result) == 1
    assert result[0].id == 'abc123'
    assert result[0].title == 'Test commit'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request_pipelines(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.pipelines.list.return_value = [
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

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_pipelines')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result) == 1
    assert result[0].id == 123
    assert result[0].status == 'success'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request_discussions(mock_get_client, mock_client, mock_merge_request):
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

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_discussions')
    result = tool.fn(project_id='1', mr_iid=1)

    assert len(result) == 1
    assert result[0].id == 'disc123'
    assert len(result[0].notes) == 1
    assert result[0].notes[0].body == 'Test note'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.remove_source_branch_after_merge = False
    mock_project.mergerequests.create.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

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
    params = mock_project.mergerequests.create.call_args.args[0]
    assert 'remove_source_branch' not in params


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_honours_project_delete_source_branch_default(
    mock_get_client, mock_client, mock_merge_request
):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.remove_source_branch_after_merge = True
    mock_project.mergerequests.create.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request')
    tool.fn(
        project_id='1',
        source_branch='feature',
        target_branch='main',
        title='Test MR',
    )

    params = mock_project.mergerequests.create.call_args.args[0]
    assert params['remove_source_branch'] is True


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_approve_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

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
    mock_get_client.return_value.get_user_project.return_value = mock_project

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
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'merge_merge_request')
    result = tool.fn(project_id='1', mr_iid=1)

    mock_merge_request.merge.assert_called_once()
    assert result.status == 'merged'
    assert result.mr_iid == 1


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project
    mock_get_client.return_value.get_user_id.return_value = 7

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request')
    result = tool.fn(
        project_id='1',
        mr_iid=1,
        title='New title',
        description='New description',
        labels=['bug'],
        assignees=['testuser'],
    )

    mock_project.mergerequests.update.assert_called_once_with(
        1,
        {
            'title': 'New title',
            'description': 'New description',
            'labels': ['bug'],
            'assignee_ids': [7],
        },
    )
    mock_get_client.return_value.get_user_id.assert_called_once_with('testuser')
    assert result.iid == 1


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request_sends_only_supplied_fields(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request')
    tool.fn(project_id='1', mr_iid=1, description='')

    mock_project.mergerequests.update.assert_called_once_with(1, {'description': ''})


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request_without_fields_does_not_touch_gitlab(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request')
    with pytest.raises(ValueError):
        tool.fn(project_id='1', mr_iid=1)

    mock_get_client.return_value.get_user_project.assert_not_called()
    mock_project.mergerequests.update.assert_not_called()


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_set_merge_request_draft_adds_prefix(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.title = 'Test MR'
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'set_merge_request_draft')
    result = tool.fn(project_id='1', mr_iid=1, draft=True)

    mock_project.mergerequests.update.assert_called_once_with(1, {'title': 'Draft: Test MR'})
    assert result.status == 'draft'
    assert result.mr_iid == 1


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_set_merge_request_draft_is_idempotent(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.title = 'Draft: Test MR'
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'set_merge_request_draft')
    result = tool.fn(project_id='1', mr_iid=1, draft=True)

    mock_project.mergerequests.update.assert_not_called()
    assert result.status == 'draft'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_set_merge_request_draft_strips_prefix(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.title = 'Draft: Test MR'
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'set_merge_request_draft')
    result = tool.fn(project_id='1', mr_iid=1, draft=False)

    mock_project.mergerequests.update.assert_called_once_with(1, {'title': 'Test MR'})
    assert result.status == 'ready'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_set_merge_request_draft_strips_legacy_wip_prefix(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.title = 'WIP: Test MR'
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'set_merge_request_draft')
    tool.fn(project_id='1', mr_iid=1, draft=False)

    mock_project.mergerequests.update.assert_called_once_with(1, {'title': 'Test MR'})


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_set_merge_request_draft_ready_is_idempotent(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.title = 'Test MR'
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'set_merge_request_draft')
    result = tool.fn(project_id='1', mr_iid=1, draft=False)

    mock_project.mergerequests.update.assert_not_called()
    assert result.status == 'ready'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request_clears_assignees(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request')
    tool.fn(project_id='1', mr_iid=1, assignees=[])

    mock_project.mergerequests.update.assert_called_once_with(1, {'assignee_ids': []})
    mock_get_client.return_value.get_user_id.assert_not_called()


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request_unknown_assignee_is_not_sent(mock_get_client, mock_client):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_get_client.return_value.get_user_project.return_value = mock_project
    mock_get_client.return_value.get_user_id.side_effect = UserNotFound('User ghost not found')

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request')
    with pytest.raises(UserNotFound):
        tool.fn(project_id='1', mr_iid=1, assignees=['ghost'])

    mock_project.mergerequests.update.assert_not_called()


def mr_with_changes(mock_merge_request, old_path='file.py', new_path='file.py'):
    mock_merge_request.changes.return_value = {
        'changes': [{'old_path': old_path, 'new_path': new_path, 'diff': '@@ -1 +1 @@\n-old\n+new'}],
        'diff_refs': {'base_sha': 'base1', 'start_sha': 'start1', 'head_sha': 'head1'},
    }
    mock_merge_request.discussions.create.return_value = discussion_with_note('Line comment')

    return mock_merge_request


def note_mock(body='Test note', note_id=1):
    note = MagicMock()
    note.attributes = {
        'id': note_id,
        'body': body,
        'author': {'username': 'testuser'},
        'created_at': '2024-01-01T00:00:00Z',
    }

    return note


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_reply_to_merge_request_discussion(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    discussion = discussion_with_note('Reply body')
    mock_merge_request.discussions.get.return_value = discussion
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'reply_to_merge_request_discussion')
    result = tool.fn(project_id='1', mr_iid=1, discussion_id='disc123', body='Reply body')

    mock_merge_request.discussions.get.assert_called_with('disc123')
    discussion.notes.create.assert_called_once_with({'body': 'Reply body'})
    assert result.id == 'disc123'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_resolve_merge_request_discussion(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    discussion = discussion_with_note('Line comment', resolved=True)
    mock_merge_request.discussions.get.return_value = discussion
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'resolve_merge_request_discussion')
    result = tool.fn(project_id='1', mr_iid=1, discussion_id='disc123')

    assert discussion.resolved is True
    discussion.save.assert_called_once()
    assert result.notes[0].resolved is True


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_unresolve_merge_request_discussion(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    discussion = discussion_with_note('Line comment')
    mock_merge_request.discussions.get.return_value = discussion
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'resolve_merge_request_discussion')
    tool.fn(project_id='1', mr_iid=1, discussion_id='disc123', resolved=False)

    assert discussion.resolved is False
    discussion.save.assert_called_once()


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_get_merge_request_notes(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.notes.list.return_value = [note_mock('First'), note_mock('Second', note_id=2)]
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'get_merge_request_notes')
    result = tool.fn(project_id='1', mr_iid=1, sort='asc')

    mock_merge_request.notes.list.assert_called_once_with(iterator=True, sort='asc')
    assert [n.body for n in result] == ['First', 'Second']


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_add_merge_request_note(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.notes.create.return_value = note_mock('Plain comment')
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'add_merge_request_note')
    result = tool.fn(project_id='1', mr_iid=1, body='Plain comment')

    mock_merge_request.notes.create.assert_called_once_with({'body': 'Plain comment'})
    assert result.body == 'Plain comment'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request_note(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    note = note_mock('Corrected')
    mock_merge_request.notes.get.return_value = note
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request_note')
    result = tool.fn(project_id='1', mr_iid=1, note_id=1, body='Corrected')

    assert note.body == 'Corrected'
    note.save.assert_called_once()
    assert result.body == 'Corrected'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_delete_merge_request_note(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'delete_merge_request_note')
    result = tool.fn(project_id='1', mr_iid=1, note_id=254230)

    mock_merge_request.notes.delete.assert_called_once_with(254230)
    assert result.status == 'deleted'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_discussion(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_merge_request.discussions.create.return_value = discussion_with_note('Thread start')
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request_discussion')
    result = tool.fn(project_id='1', mr_iid=1, body='Thread start')

    mock_merge_request.discussions.create.assert_called_once_with({'body': 'Thread start'})
    assert result.individual_note is False


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_line_discussion(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mr_with_changes(mock_merge_request)
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request_line_discussion')
    result = tool.fn(project_id='1', mr_iid=1, body='Line comment', file='file.py', line=13)

    mock_merge_request.discussions.create.assert_called_once_with({
        'body': 'Line comment',
        'position': {
            'base_sha': 'base1',
            'start_sha': 'start1',
            'head_sha': 'head1',
            'position_type': 'text',
            'new_path': 'file.py',
            'old_path': 'file.py',
            'new_line': 13,
        },
    })
    assert result.id == 'disc123'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_line_discussion_on_removed_line(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mr_with_changes(mock_merge_request)
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request_line_discussion')
    tool.fn(project_id='1', mr_iid=1, body='Line comment', file='file.py', line=7, side='old')

    position = mock_merge_request.discussions.create.call_args.args[0]['position']
    assert position['old_line'] == 7
    assert 'new_line' not in position


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_line_discussion_rejects_unknown_side(mock_get_client, mock_client):
    mcp = FastMCP('test')

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request_line_discussion')
    with pytest.raises(ValueError):
        tool.fn(project_id='1', mr_iid=1, body='Line comment', file='file.py', line=1, side='sideways')

    mock_get_client.assert_not_called()


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_line_discussion_resolves_renamed_paths(
    mock_get_client, mock_client, mock_merge_request
):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mr_with_changes(
        mock_merge_request, old_path='before.py', new_path='after.py'
    )
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request_line_discussion')
    tool.fn(project_id='1', mr_iid=1, body='Line comment', file='before.py', line=5)

    position = mock_merge_request.discussions.create.call_args.args[0]['position']
    assert position['old_path'] == 'before.py'
    assert position['new_path'] == 'after.py'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_create_merge_request_line_discussion_rejects_unchanged_file(
    mock_get_client, mock_client, mock_merge_request
):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mr_with_changes(mock_merge_request)
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'create_merge_request_line_discussion')
    with pytest.raises(ValueError):
        tool.fn(project_id='1', mr_iid=1, body='Line comment', file='untouched.py', line=1)

    mock_merge_request.discussions.create.assert_not_called()


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_update_merge_request_discussion_note(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    discussion = discussion_with_note('Corrected reply')
    note = note_mock('Corrected reply')
    discussion.notes.get.return_value = note
    mock_merge_request.discussions.get.return_value = discussion
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'update_merge_request_discussion_note')
    result = tool.fn(project_id='1', mr_iid=1, discussion_id='disc123', note_id=1, body='Corrected reply')

    assert note.body == 'Corrected reply'
    note.save.assert_called_once()
    assert result.notes[0].body == 'Corrected reply'


@patch('gitlab_mcp.tools.merge_requests.get_client')
def test_delete_merge_request_discussion_note(mock_get_client, mock_client, mock_merge_request):
    mcp = FastMCP('test')
    mock_project = MagicMock()
    discussion = discussion_with_note('Line comment')
    mock_merge_request.discussions.get.return_value = discussion
    mock_project.mergerequests.get.return_value = mock_merge_request
    mock_get_client.return_value.get_user_project.return_value = mock_project

    merge_requests.register_tools(mcp, mock_client, GITLAB_URL)

    tool = next(t for t in mcp._tool_manager._tools.values() if t.name == 'delete_merge_request_discussion_note')
    result = tool.fn(project_id='1', mr_iid=1, discussion_id='disc123', note_id=254230)

    discussion.notes.delete.assert_called_once_with(254230)
    mock_merge_request.notes.delete.assert_not_called()
    assert result.status == 'deleted'
