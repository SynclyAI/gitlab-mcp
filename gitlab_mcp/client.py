import gitlab
from pathlib import Path


class GitLabClient:
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
