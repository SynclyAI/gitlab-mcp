import pytest
from unittest.mock import MagicMock, patch

from gitlab_mcp.client import CompositeGitLabClient, PermissionDenied, TokenGitLabClient


@patch('gitlab_mcp.client.gitlab.Gitlab')
def test_token_client_init(mock_gitlab_class):
    mock_gitlab = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab

    client = TokenGitLabClient('https://gitlab.example.com', 'test-token')

    mock_gitlab_class.assert_called_once_with(
        url='https://gitlab.example.com',
        private_token='test-token',
        ssl_verify=True,
    )


@patch('gitlab_mcp.client.OAuthGitLabClient')
def test_composite_client_both_have_access(mock_oauth_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.return_value = MagicMock()
    mock_oauth_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()
    mock_service_client.get_project.return_value = MagicMock()

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
    )

    client.get_project('1')

    mock_user_client.get_project.assert_called_once_with('1')
    mock_service_client.get_project.assert_called_once_with('1')


@patch('gitlab_mcp.client.OAuthGitLabClient')
def test_composite_client_user_denied(mock_oauth_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.side_effect = Exception('Not found')
    mock_oauth_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
    )

    with pytest.raises(PermissionDenied, match='User cannot access'):
        client.get_project('1')


@patch('gitlab_mcp.client.OAuthGitLabClient')
def test_composite_client_service_denied(mock_oauth_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.return_value = MagicMock()
    mock_oauth_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()
    mock_service_client.get_project.side_effect = Exception('Not found')

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
    )

    with pytest.raises(PermissionDenied, match='AI not enabled'):
        client.get_project('1')


@patch('gitlab_mcp.client.OAuthGitLabClient')
def test_composite_client_get_user_project(mock_oauth_client_class):
    mock_user_client = MagicMock()
    mock_project = MagicMock()
    mock_user_client.get_project.return_value = mock_project
    mock_oauth_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
    )

    result = client.get_user_project('1')

    mock_user_client.get_project.assert_called_once_with('1')
    assert result == mock_project


@patch('gitlab_mcp.client.OAuthGitLabClient')
def test_composite_client_get_user_project_denied(mock_oauth_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.side_effect = Exception('Not found')
    mock_oauth_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
    )

    with pytest.raises(PermissionDenied, match='User cannot access'):
        client.get_user_project('1')


@patch('gitlab_mcp.client.OAuthGitLabClient')
def test_composite_client_list_projects(mock_oauth_client_class):
    mock_service_client = MagicMock()
    mock_service_client.list_projects.return_value = [MagicMock()]

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
    )

    result = client.list_projects()

    mock_service_client.list_projects.assert_called_once()
    assert len(result) == 1
