import pytest
from unittest.mock import MagicMock, patch

from gitlab_mcp.auth import check_project_access, PermissionDenied
from gitlab_mcp.config import Config, Secrets


@pytest.fixture
def mock_config():
    secrets = Secrets(
        oauth_client_id='client_id',
        oauth_client_secret='client_secret',
        service_token='service_token',
    )

    return Config(
        url='https://gitlab.example.com',
        secrets=secrets,
        ca_cert_path=None,
    )


def test_check_project_access_both_have_access(mock_config):
    with patch('gitlab_mcp.auth.GitLabClient') as mock_client_class:
        mock_user_client = MagicMock()
        mock_service_client = MagicMock()
        mock_client_class.return_value = mock_user_client

        check_project_access('1', 'user_token', mock_service_client, mock_config)

        mock_user_client.get_project.assert_called_once_with('1')
        mock_service_client.get_project.assert_called_once_with('1')


def test_check_project_access_user_denied(mock_config):
    with patch('gitlab_mcp.auth.GitLabClient') as mock_client_class:
        mock_user_client = MagicMock()
        mock_user_client.get_project.side_effect = Exception('Not found')
        mock_service_client = MagicMock()
        mock_client_class.return_value = mock_user_client

        with pytest.raises(PermissionDenied, match='User cannot access'):
            check_project_access('1', 'user_token', mock_service_client, mock_config)


def test_check_project_access_service_denied(mock_config):
    with patch('gitlab_mcp.auth.GitLabClient') as mock_client_class:
        mock_user_client = MagicMock()
        mock_service_client = MagicMock()
        mock_service_client.get_project.side_effect = Exception('Not found')
        mock_client_class.return_value = mock_user_client

        with pytest.raises(PermissionDenied, match='AI not enabled'):
            check_project_access('1', 'user_token', mock_service_client, mock_config)
