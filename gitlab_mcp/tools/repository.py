from __future__ import annotations

from dataclasses import dataclass

from fastmcp import FastMCP
from gitlab.v4.objects import Project as GitLabProject, ProjectBranch, ProjectCommit

from gitlab_mcp.client import TokenGitLabClient
from gitlab_mcp.tools.common import get_client


def decode_text(file) -> str:
    try:
        return file.decode().decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError(f'File {file.file_path} is not UTF-8 text ({file.size} bytes)')


def read_lines(text: str, start_line: int | None, line_count: int | None) -> tuple[str, int, int]:
    lines = text.splitlines()
    total_lines = len(lines)
    if start_line is None and line_count is None:
        return text, total_lines, 1

    start = start_line if start_line is not None else 1
    if start < 1:
        raise ValueError(f'start_line must be 1 or greater, got {start}')
    if line_count is not None and line_count < 1:
        raise ValueError(f'line_count must be 1 or greater, got {line_count}')
    if start_line is not None and start > total_lines:
        raise ValueError(f'File has {total_lines} lines, start_line {start} is past the end')

    end = start - 1 + line_count if line_count is not None else total_lines

    return '\n'.join(lines[start - 1:end]), total_lines, start


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
    total_lines: int
    start_line: int


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
        start_line: int | None = None,
        line_count: int | None = None,
    ) -> FileContent:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        file = project.files.get(file_path, ref or project.default_branch)
        content, total_lines, start = read_lines(decode_text(file), start_line, line_count)

        return FileContent(
            file_path=file.file_path,
            file_name=file.file_name,
            size=file.size,
            encoding=file.encoding,
            content=content,
            ref=file.ref,
            last_commit_id=file.last_commit_id,
            total_lines=total_lines,
            start_line=start,
        )

    @mcp.tool
    def get_file_blame(
        project_id: str,
        file_path: str,
        ref: str | None = None,
    ) -> list[BlameEntry]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        blame = project.files.blame(file_path, ref or project.default_branch)

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
