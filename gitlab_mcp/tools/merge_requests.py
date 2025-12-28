from fastmcp import FastMCP

from gitlab_mcp.client import GitLabClient


def register_tools(mcp: FastMCP, client: GitLabClient):

    @mcp.tool
    def list_merge_requests(
        project_id: str,
        state: str | None = None,
        author_username: str | None = None,
        assignee_username: str | None = None,
    ) -> list[dict]:
        project = client.get_project(project_id)
        params = {'iterator': True}
        if state:
            params['state'] = state
        if author_username:
            params['author_username'] = author_username
        if assignee_username:
            params['assignee_username'] = assignee_username

        mrs = project.mergerequests.list(**params)

        return [_serialize_mr(mr) for mr in mrs]

    @mcp.tool
    def get_merge_request(
        project_id: str,
        mr_iid: int,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)

        return _serialize_mr_details(mr)

    @mcp.tool
    def get_merge_request_changes(
        project_id: str,
        mr_iid: int,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        changes = mr.changes()

        return {
            'changes': [
                {
                    'old_path': c['old_path'],
                    'new_path': c['new_path'],
                    'a_mode': c['a_mode'],
                    'b_mode': c['b_mode'],
                    'new_file': c['new_file'],
                    'renamed_file': c['renamed_file'],
                    'deleted_file': c['deleted_file'],
                    'diff': c['diff'],
                }
                for c in changes['changes']
            ]
        }

    @mcp.tool
    def get_mr_commits(
        project_id: str,
        mr_iid: int,
    ) -> list[dict]:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        commits = mr.commits()

        return [
            {
                'id': c['id'],
                'short_id': c['short_id'],
                'title': c['title'],
                'message': c['message'],
                'author_name': c['author_name'],
                'author_email': c['author_email'],
                'authored_date': c['authored_date'],
                'committed_date': c['committed_date'],
            }
            for c in commits
        ]

    @mcp.tool
    def get_mr_pipelines(
        project_id: str,
        mr_iid: int,
    ) -> list[dict]:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        pipelines = mr.pipelines()

        return [
            {
                'id': p['id'],
                'sha': p['sha'],
                'ref': p['ref'],
                'status': p['status'],
                'web_url': p['web_url'],
                'created_at': p['created_at'],
                'updated_at': p['updated_at'],
            }
            for p in pipelines
        ]

    @mcp.tool
    def get_mr_discussions(
        project_id: str,
        mr_iid: int,
    ) -> list[dict]:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        discussions = mr.discussions.list(iterator=True)

        return [
            {
                'id': d.id,
                'individual_note': d.individual_note,
                'notes': [
                    {
                        'id': n['id'],
                        'body': n['body'],
                        'author': n['author']['username'],
                        'created_at': n['created_at'],
                        'updated_at': n['updated_at'],
                        'system': n['system'],
                        'resolvable': n['resolvable'],
                        'resolved': n.get('resolved', False),
                        'position': n.get('position'),
                    }
                    for n in d.attributes['notes']
                ],
            }
            for d in discussions
        ]

    @mcp.tool
    def add_mr_discussion(
        project_id: str,
        mr_iid: int,
        body: str,
        position: dict | None = None,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        params = {'body': body}
        if position:
            params['position'] = position

        discussion = mr.discussions.create(params)

        return {
            'id': discussion.id,
            'notes': [
                {
                    'id': n['id'],
                    'body': n['body'],
                    'author': n['author']['username'],
                    'created_at': n['created_at'],
                }
                for n in discussion.attributes['notes']
            ],
        }

    @mcp.tool
    def add_merge_request_comment(
        project_id: str,
        mr_iid: int,
        body: str,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        note = mr.notes.create({'body': body})

        return {
            'id': note.id,
            'body': note.body,
            'author': note.author['username'],
            'created_at': note.created_at,
        }

    @mcp.tool
    def create_merge_request(
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str | None = None,
    ) -> dict:
        project = client.get_project(project_id)
        params = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title,
        }
        if description:
            params['description'] = description

        mr = project.mergerequests.create(params)

        return _serialize_mr_details(mr)

    @mcp.tool
    def approve_merge_request(
        project_id: str,
        mr_iid: int,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.approve()

        return {'status': 'approved', 'mr_iid': mr_iid}

    @mcp.tool
    def unapprove_merge_request(
        project_id: str,
        mr_iid: int,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.unapprove()

        return {'status': 'unapproved', 'mr_iid': mr_iid}

    @mcp.tool
    def merge_merge_request(
        project_id: str,
        mr_iid: int,
        should_remove_source_branch: bool = False,
    ) -> dict:
        project = client.get_project(project_id)
        mr = project.mergerequests.get(mr_iid)
        params = {}
        if should_remove_source_branch:
            params['should_remove_source_branch'] = True

        mr.merge(**params)

        return {'status': 'merged', 'mr_iid': mr_iid}


def _serialize_mr(mr) -> dict:
    return {
        'iid': mr.iid,
        'title': mr.title,
        'state': mr.state,
        'author': mr.author['username'],
        'source_branch': mr.source_branch,
        'target_branch': mr.target_branch,
        'web_url': mr.web_url,
        'created_at': mr.created_at,
        'updated_at': mr.updated_at,
    }


def _serialize_mr_details(mr) -> dict:
    return {
        'iid': mr.iid,
        'title': mr.title,
        'description': mr.description,
        'state': mr.state,
        'author': mr.author['username'],
        'source_branch': mr.source_branch,
        'target_branch': mr.target_branch,
        'web_url': mr.web_url,
        'created_at': mr.created_at,
        'updated_at': mr.updated_at,
        'merged_by': mr.merged_by['username'] if mr.merged_by else None,
        'merged_at': mr.merged_at,
        'labels': mr.labels,
        'milestone': mr.milestone['title'] if mr.milestone else None,
        'assignees': [a['username'] for a in mr.assignees],
        'reviewers': [r['username'] for r in mr.reviewers],
        'draft': mr.draft,
        'work_in_progress': mr.work_in_progress,
        'has_conflicts': mr.has_conflicts,
        'blocking_discussions_resolved': mr.blocking_discussions_resolved,
    }
