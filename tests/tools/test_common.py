import gitlab.exceptions
from mcp.types import CallToolResult, TextContent

from gitlab_mcp.client import PermissionDenied, ProjectNotFound
from gitlab_mcp.tools.common import handle_gitlab_errors


def test_handle_gitlab_errors_success():
    @handle_gitlab_errors
    def success_func():
        return 'success'

    result = success_func()

    assert result == 'success'


def test_handle_gitlab_errors_project_not_found():
    @handle_gitlab_errors
    def raise_project_not_found():
        raise ProjectNotFound('Project 123 not found')

    result = raise_project_not_found()

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Project 123 not found' in result.content[0].text


def test_handle_gitlab_errors_permission_denied():
    @handle_gitlab_errors
    def raise_permission_denied():
        raise PermissionDenied('Access denied')

    result = raise_permission_denied()

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert 'Access denied' in result.content[0].text


def test_handle_gitlab_errors_gitlab_error():
    @handle_gitlab_errors
    def raise_gitlab_error():
        raise gitlab.exceptions.GitlabCreateError('500: Internal Server Error')

    result = raise_gitlab_error()

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert '500' in result.content[0].text
