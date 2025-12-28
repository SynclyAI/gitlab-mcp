import pytest
from unittest.mock import MagicMock, patch

from gitlab_mcp.client import CompositeGitLabClient, PermissionDenied


@patch('gitlab_mcp.client.TokenGitLabClient')
def test_composite_client_both_have_access(mock_token_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.return_value = MagicMock()
    mock_token_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()
    mock_service_client.get_project.return_value = MagicMock()

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
        None,
    )

    client.get_project('1')

    mock_user_client.get_project.assert_called_once_with('1')
    mock_service_client.get_project.assert_called_once_with('1')


@patch('gitlab_mcp.client.TokenGitLabClient')
def test_composite_client_user_denied(mock_token_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.side_effect = Exception('Not found')
    mock_token_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
        None,
    )

    with pytest.raises(PermissionDenied, match='User cannot access'):
        client.get_project('1')


@patch('gitlab_mcp.client.TokenGitLabClient')
def test_composite_client_service_denied(mock_token_client_class):
    mock_user_client = MagicMock()
    mock_user_client.get_project.return_value = MagicMock()
    mock_token_client_class.return_value = mock_user_client

    mock_service_client = MagicMock()
    mock_service_client.get_project.side_effect = Exception('Not found')

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
        None,
    )

    with pytest.raises(PermissionDenied, match='AI not enabled'):
        client.get_project('1')


@patch('gitlab_mcp.client.TokenGitLabClient')
def test_composite_client_list_projects(mock_token_client_class):
    mock_service_client = MagicMock()
    mock_service_client.list_projects.return_value = [MagicMock()]

    client = CompositeGitLabClient(
        'user_token',
        mock_service_client,
        'https://gitlab.example.com',
        None,
    )

    result = client.list_projects()

    mock_service_client.list_projects.assert_called_once()
    assert len(result) == 1
