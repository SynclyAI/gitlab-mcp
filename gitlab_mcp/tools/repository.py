from fastmcp import FastMCP

from gitlab_mcp.client import TokenGitLabClient
from gitlab_mcp.models import (
    BlameCommit,
    BlameEntry,
    Branch,
    CodeSearchResult,
    CommitDetails,
    CommitListItem,
    FileContent,
    Project,
    TreeItem,
)
from gitlab_mcp.tools.common import get_client


def register_tools(
    mcp: FastMCP,
    service_client: TokenGitLabClient,
    url: str,
):

    @mcp.tool
    def list_projects(
        search: str | None = None,
        owned: bool | None = None,
        membership: bool | None = None,
    ) -> list[Project]:
        client = get_client(service_client, url)
        params = {'iterator': True}
        if search:
            params['search'] = search
        if owned is not None:
            params['owned'] = owned
        if membership is not None:
            params['membership'] = membership

        projects = client.list_projects(**params)

        return [Project.model_validate(p, from_attributes=True) for p in projects]

    @mcp.tool
    def get_repository_tree(
        project_id: str,
        path: str | None = None,
        ref: str | None = None,
        recursive: bool = False,
    ) -> list[TreeItem]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {'iterator': True, 'recursive': recursive}
        if path:
            params['path'] = path
        if ref:
            params['ref'] = ref

        items = project.repository_tree(**params)

        return [TreeItem(**item) for item in items]

    @mcp.tool
    def get_file_content(
        project_id: str,
        file_path: str,
        ref: str | None = None,
    ) -> FileContent:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {'file_path': file_path}
        if ref:
            params['ref'] = ref

        file = project.files.get(**params)

        return FileContent(
            file_path=file.file_path,
            file_name=file.file_name,
            size=file.size,
            encoding=file.encoding,
            content=file.decode().decode('utf-8'),
            ref=file.ref,
            last_commit_id=file.last_commit_id,
        )

    @mcp.tool
    def get_file_blame(
        project_id: str,
        file_path: str,
        ref: str | None = None,
    ) -> list[BlameEntry]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {}
        if ref:
            params['ref'] = ref

        blame = project.files.blame(file_path, **params)

        return [
            BlameEntry(
                commit=BlameCommit(**entry['commit']),
                lines=entry['lines'],
            )
            for entry in blame
        ]

    @mcp.tool
    def search_code(
        project_id: str,
        query: str,
        ref: str | None = None,
    ) -> list[CodeSearchResult]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {'scope': 'blobs', 'search': query}
        if ref:
            params['ref'] = ref

        results = project.search(**params)

        return [CodeSearchResult(**r) for r in results]

    @mcp.tool
    def list_branches(
        project_id: str,
        search: str | None = None,
    ) -> list[Branch]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {'iterator': True}
        if search:
            params['search'] = search

        branches = project.branches.list(**params)

        return [Branch.model_validate(b, from_attributes=True) for b in branches]

    @mcp.tool
    def list_commits(
        project_id: str,
        ref_name: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[CommitListItem]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {'iterator': True}
        if ref_name:
            params['ref_name'] = ref_name
        if since:
            params['since'] = since
        if until:
            params['until'] = until

        commits = project.commits.list(**params)

        return [CommitListItem.model_validate(c, from_attributes=True) for c in commits]

    @mcp.tool
    def get_commit(
        project_id: str,
        sha: str,
    ) -> CommitDetails:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        commit = project.commits.get(sha)

        return CommitDetails.model_validate(commit, from_attributes=True)
