import pytest
from unittest.mock import MagicMock

from gitlab_mcp.client import TokenGitLabClient


@pytest.fixture
def mock_client():
    return MagicMock(spec=TokenGitLabClient)


@pytest.fixture
def mock_project():
    project = MagicMock()
    project.id = 1
    project.name = 'test-project'
    project.path_with_namespace = 'group/test-project'
    project.web_url = 'https://gitlab.example.com/group/test-project'
    project.description = 'Test project'

    return project


@pytest.fixture
def mock_merge_request():
    mr = MagicMock()
    mr.iid = 1
    mr.title = 'Test MR'
    mr.description = 'Test description'
    mr.state = 'opened'
    mr.author = {'username': 'testuser'}
    mr.source_branch = 'feature'
    mr.target_branch = 'main'
    mr.web_url = 'https://gitlab.example.com/group/test-project/-/merge_requests/1'
    mr.created_at = '2024-01-01T00:00:00Z'
    mr.updated_at = '2024-01-01T00:00:00Z'
    mr.merged_by = None
    mr.merged_at = None
    mr.labels = []
    mr.milestone = None
    mr.assignees = []
    mr.reviewers = []
    mr.draft = False
    mr.work_in_progress = False
    mr.has_conflicts = False
    mr.blocking_discussions_resolved = True

    return mr
