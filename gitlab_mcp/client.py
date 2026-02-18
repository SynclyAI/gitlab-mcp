import os

import gitlab
from abc import ABC, abstractmethod


class PermissionDenied(Exception):
    pass


class ProjectNotFound(Exception):
    pass


class GitLabClient(ABC):
    @abstractmethod
    def get_project(self, project_id: str | int):
        pass

    @abstractmethod
    def list_projects(self, **kwargs):
        pass

    @abstractmethod
    def list_merge_requests(self, **kwargs):
        pass


class TokenGitLabClient(GitLabClient):
    def __init__(self, url: str, token: str):
        self._gl = gitlab.Gitlab(
            url=url,
            private_token=token,
            ssl_verify=os.environ.get('SSL_CERT_FILE', True),
        )

    def get_project(self, project_id: str | int):
        return self._gl.projects.get(project_id)

    def list_projects(self, **kwargs):
        return self._gl.projects.list(**kwargs)

    def list_merge_requests(self, **kwargs):
        return self._gl.mergerequests.list(**kwargs)

    def get_current_user(self):
        return self._gl.user

    def auth(self):
        self._gl.auth()


class OAuthGitLabClient(GitLabClient):
    def __init__(self, url: str, oauth_token: str):
        self._gl = gitlab.Gitlab(
            url=url,
            oauth_token=oauth_token,
            ssl_verify=os.environ.get('SSL_CERT_FILE', True),
        )

    def get_project(self, project_id: str | int):
        return self._gl.projects.get(project_id)

    def list_projects(self, **kwargs):
        return self._gl.projects.list(**kwargs)

    def list_merge_requests(self, **kwargs):
        return self._gl.mergerequests.list(**kwargs)


class CompositeGitLabClient(GitLabClient):
    def __init__(
        self,
        user_token: str,
        service_client: TokenGitLabClient,
        url: str,
    ):
        self._user_client = OAuthGitLabClient(url, user_token)
        self._service_client = service_client

    def get_project(self, project_id: str | int):
        try:
            return self._service_client.get_project(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            if e.response_code == 404:
                raise ProjectNotFound(f'Project {project_id} not found')

            raise PermissionDenied(f'Service account cannot access project {project_id}')

    def get_user_project(self, project_id: str | int):
        try:
            return self._user_client.get_project(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            if e.response_code == 404:
                raise ProjectNotFound(f'Project {project_id} not found')
            raise PermissionDenied(f'User cannot access project {project_id}')

    def list_projects(self, **kwargs):
        return self._service_client.list_projects(**kwargs)

    def list_merge_requests(self, **kwargs):
        return self._service_client.list_merge_requests(**kwargs)
