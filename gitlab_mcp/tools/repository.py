from __future__ import annotations

from dataclasses import dataclass

from fastmcp import FastMCP
from gitlab.v4.objects import Project as GitLabProject, ProjectBranch, ProjectCommit

from gitlab_mcp.client import TokenGitLabClient
from gitlab_mcp.tools.common import get_client


@dataclass
class Project:
    id: int
    name: str
    path_with_namespace: str
    web_url: str
    description: str | None

    @staticmethod
    def from_gitlab(p: GitLabProject) -> Project:
        return Project(
            id=p.id,
            name=p.name,
            path_with_namespace=p.path_with_namespace,
            web_url=p.web_url,
            description=p.description,
        )


@dataclass
class TreeItem:
    id: str
    name: str
    type: str
    path: str
    mode: str

    @staticmethod
    def from_dict(item: dict) -> TreeItem:
        return TreeItem(
            id=item['id'],
            name=item['name'],
            type=item['type'],
            path=item['path'],
            mode=item['mode'],
        )


@dataclass
class FileContent:
    file_path: str
    file_name: str
    size: int
    encoding: str
    content: str
    ref: str
    last_commit_id: str


@dataclass
class BlameCommit:
    id: str
    author_name: str
    author_email: str
    message: str
    committed_date: str


@dataclass
class BlameEntry:
    commit: BlameCommit
    lines: list[str]


@dataclass
class CodeSearchResult:
    basename: str
    data: str
    path: str
    filename: str
    ref: str
    startline: int
    project_id: int

    @staticmethod
    def from_dict(r: dict) -> CodeSearchResult:
        return CodeSearchResult(
            basename=r['basename'],
            data=r['data'],
            path=r['path'],
            filename=r['filename'],
            ref=r['ref'],
            startline=r['startline'],
            project_id=r['project_id'],
        )


@dataclass
class BranchCommit:
    id: str
    short_id: str
    title: str
    author_name: str
    committed_date: str


@dataclass
class Branch:
    name: str
    merged: bool
    protected: bool
    default: bool
    web_url: str
    commit: BranchCommit

    @staticmethod
    def from_gitlab(b: ProjectBranch) -> Branch:
        return Branch(
            name=b.name,
            merged=b.merged,
            protected=b.protected,
            default=b.default,
            web_url=b.web_url,
            commit=BranchCommit(**b.commit),
        )


@dataclass
class CommitListItem:
    id: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    authored_date: str
    committer_name: str
    committed_date: str
    web_url: str

    @staticmethod
    def from_gitlab(c: ProjectCommit) -> CommitListItem:
        return CommitListItem(
            id=c.id,
            short_id=c.short_id,
            title=c.title,
            message=c.message,
            author_name=c.author_name,
            author_email=c.author_email,
            authored_date=c.authored_date,
            committer_name=c.committer_name,
            committed_date=c.committed_date,
            web_url=c.web_url,
        )


@dataclass
class CommitDetails:
    id: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    authored_date: str
    committed_date: str
    committer_name: str
    web_url: str
    parent_ids: list[str] | None = None
    stats: dict | None = None

    @staticmethod
    def from_gitlab(c: ProjectCommit) -> CommitDetails:
        return CommitDetails(
            id=c.id,
            short_id=c.short_id,
            title=c.title,
            message=c.message,
            author_name=c.author_name,
            author_email=c.author_email,
            authored_date=c.authored_date,
            committer_name=c.committer_name,
            committed_date=c.committed_date,
            web_url=c.web_url,
            parent_ids=c.parent_ids,
            stats=c.stats,
        )


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

        return [Project.from_gitlab(p) for p in projects]

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

        return [TreeItem.from_dict(item) for item in items]

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

        return [CodeSearchResult.from_dict(r) for r in results]

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

        return [Branch.from_gitlab(b) for b in branches]

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

        return [CommitListItem.from_gitlab(c) for c in commits]

    @mcp.tool
    def get_commit(
        project_id: str,
        sha: str,
    ) -> CommitDetails:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        commit = project.commits.get(sha)

        return CommitDetails.from_gitlab(commit)
