import gitlab
from abc import ABC, abstractmethod
from pathlib import Path


class PermissionDenied(Exception):
    pass


class GitLabClient(ABC):
    @abstractmethod
    def get_project(self, project_id: str | int):
        pass

    @abstractmethod
    def list_projects(self, **kwargs):
        pass


class TokenGitLabClient(GitLabClient):
    def __init__(self, url: str, token: str, ca_cert_path: Path | None = None):
        ssl_verify: bool | str = True
        if ca_cert_path:
            ssl_verify = str(ca_cert_path)

        self._gl = gitlab.Gitlab(url=url, private_token=token, ssl_verify=ssl_verify)

    def get_project(self, project_id: str | int):
        return self._gl.projects.get(project_id)

    def list_projects(self, **kwargs):
        return self._gl.projects.list(**kwargs)

    def get_current_user(self):
        return self._gl.user

    def auth(self):
        self._gl.auth()


class CompositeGitLabClient(GitLabClient):
    def __init__(
        self,
        user_token: str,
        service_client: TokenGitLabClient,
        url: str,
        ca_cert_path: Path | None,
    ):
        self._user_client = TokenGitLabClient(url, user_token, ca_cert_path)
        self._service_client = service_client

    def get_project(self, project_id: str | int):
        try:
            self._user_client.get_project(project_id)
        except Exception:
            raise PermissionDenied(f'User cannot access project {project_id}')

        try:
            return self._service_client.get_project(project_id)
        except Exception:
            raise PermissionDenied(f'AI not enabled for project {project_id}')

    def list_projects(self, **kwargs):
        return self._service_client.list_projects(**kwargs)
