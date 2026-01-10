from fastmcp import FastMCP

from gitlab_mcp.client import TokenGitLabClient
from gitlab_mcp.models import (
    ActionResult,
    Commit,
    Discussion,
    MergeRequest,
    MergeRequestChange,
    MergeRequestChanges,
    MergeRequestDetails,
    Note,
    Pipeline,
)
from gitlab_mcp.tools.common import get_client


def register_tools(
    mcp: FastMCP,
    service_client: TokenGitLabClient,
    url: str,
):

    @mcp.tool
    def search_merge_requests(
        state: str | None = None,
        scope: str = 'all',
        author_username: str | None = None,
        assignee_username: str | None = None,
        search: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
    ) -> list[MergeRequest]:
        client = get_client(service_client, url)
        params = {'iterator': True, 'scope': scope}
        if state:
            params['state'] = state
        if author_username:
            params['author_username'] = author_username
        if assignee_username:
            params['assignee_username'] = assignee_username
        if search:
            params['search'] = search
        if created_after:
            params['created_after'] = created_after
        if created_before:
            params['created_before'] = created_before
        if updated_after:
            params['updated_after'] = updated_after
        if updated_before:
            params['updated_before'] = updated_before

        mrs = client.list_merge_requests(**params)

        return [MergeRequest.model_validate(mr, from_attributes=True) for mr in mrs]

    @mcp.tool
    def list_merge_requests(
        project_id: str,
        state: str | None = None,
        author_username: str | None = None,
        assignee_username: str | None = None,
    ) -> list[MergeRequest]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {'iterator': True}
        if state:
            params['state'] = state
        if author_username:
            params['author_username'] = author_username
        if assignee_username:
            params['assignee_username'] = assignee_username

        mrs = project.mergerequests.list(**params)

        return [MergeRequest.model_validate(mr, from_attributes=True) for mr in mrs]

    @mcp.tool
    def get_merge_request(
        project_id: str,
        mr_iid: int,
    ) -> MergeRequestDetails:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)

        return MergeRequestDetails.model_validate(mr, from_attributes=True)

    @mcp.tool
    def get_merge_request_changes(
        project_id: str,
        mr_iid: int,
    ) -> MergeRequestChanges:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        changes = mr.changes()

        return MergeRequestChanges(
            changes=[MergeRequestChange(**c) for c in changes['changes']]
        )

    @mcp.tool
    def get_mr_commits(
        project_id: str,
        mr_iid: int,
    ) -> list[Commit]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        commits = mr.commits()

        return [Commit(**c) for c in commits]

    @mcp.tool
    def get_mr_pipelines(
        project_id: str,
        mr_iid: int,
    ) -> list[Pipeline]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        pipelines = mr.pipelines()

        return [Pipeline(**p) for p in pipelines]

    @mcp.tool
    def get_mr_discussions(
        project_id: str,
        mr_iid: int,
    ) -> list[Discussion]:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        discussions = mr.discussions.list(iterator=True)

        return [
            Discussion(
                id=d.id,
                individual_note=d.individual_note,
                notes=[Note(**n) for n in d.attributes['notes']],
            )
            for d in discussions
        ]

    @mcp.tool
    def add_mr_discussion(
        project_id: str,
        mr_iid: int,
        body: str,
        position: dict | None = None,
    ) -> Discussion:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        params = {'body': body}
        if position:
            params['position'] = position

        discussion = mr.discussions.create(params)

        return Discussion(
            id=discussion.id,
            individual_note=False,
            notes=[Note(**n) for n in discussion.attributes['notes']],
        )

    @mcp.tool
    def add_merge_request_comment(
        project_id: str,
        mr_iid: int,
        body: str,
    ) -> Note:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        note = mr.notes.create({'body': body})

        return Note(
            id=note.id,
            body=note.body,
            author=note.author['username'],
            created_at=note.created_at,
        )

    @mcp.tool
    def create_merge_request(
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str | None = None,
    ) -> MergeRequestDetails:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        params = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title,
        }
        if description:
            params['description'] = description

        mr = project.mergerequests.create(params)

        return MergeRequestDetails.model_validate(mr, from_attributes=True)

    @mcp.tool
    def approve_merge_request(
        project_id: str,
        mr_iid: int,
    ) -> ActionResult:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.approve()

        return ActionResult(status='approved', mr_iid=mr_iid)

    @mcp.tool
    def unapprove_merge_request(
        project_id: str,
        mr_iid: int,
    ) -> ActionResult:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.unapprove()

        return ActionResult(status='unapproved', mr_iid=mr_iid)

    @mcp.tool
    def merge_merge_request(
        project_id: str,
        mr_iid: int,
        should_remove_source_branch: bool = False,
    ) -> ActionResult:
        client = get_client(service_client, url)
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        params = {}
        if should_remove_source_branch:
            params['should_remove_source_branch'] = True

        mr.merge(**params)

        return ActionResult(status='merged', mr_iid=mr_iid)
