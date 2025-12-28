from fastmcp import FastMCP

from gitlab_mcp.client import GitLabClient


def register_tools(mcp: FastMCP, client: GitLabClient):

    @mcp.tool
    def list_projects(
        search: str | None = None,
        owned: bool | None = None,
        membership: bool | None = None,
    ) -> list[dict]:
        params = {'iterator': True}
        if search:
            params['search'] = search
        if owned is not None:
            params['owned'] = owned
        if membership is not None:
            params['membership'] = membership

        projects = client.list_projects(**params)

        return [
            {
                'id': p.id,
                'name': p.name,
                'path_with_namespace': p.path_with_namespace,
                'web_url': p.web_url,
                'description': p.description,
            }
            for p in projects
        ]

    @mcp.tool
    def get_repository_tree(
        project_id: str,
        path: str | None = None,
        ref: str | None = None,
        recursive: bool = False,
    ) -> list[dict]:
        project = client.get_project(project_id)
        params = {'iterator': True, 'recursive': recursive}
        if path:
            params['path'] = path
        if ref:
            params['ref'] = ref

        items = project.repository_tree(**params)

        return [
            {
                'id': item['id'],
                'name': item['name'],
                'type': item['type'],
                'path': item['path'],
                'mode': item['mode'],
            }
            for item in items
        ]

    @mcp.tool
    def get_file_content(
        project_id: str,
        file_path: str,
        ref: str | None = None,
    ) -> dict:
        project = client.get_project(project_id)
        params = {'file_path': file_path}
        if ref:
            params['ref'] = ref

        file = project.files.get(**params)

        return {
            'file_path': file.file_path,
            'file_name': file.file_name,
            'size': file.size,
            'encoding': file.encoding,
            'content': file.decode().decode('utf-8'),
            'ref': file.ref,
            'last_commit_id': file.last_commit_id,
        }

    @mcp.tool
    def get_file_blame(
        project_id: str,
        file_path: str,
        ref: str | None = None,
    ) -> list[dict]:
        project = client.get_project(project_id)
        params = {}
        if ref:
            params['ref'] = ref

        blame = project.files.blame(file_path, **params)

        return [
            {
                'commit': {
                    'id': entry['commit']['id'],
                    'author_name': entry['commit']['author_name'],
                    'author_email': entry['commit']['author_email'],
                    'message': entry['commit']['message'],
                    'committed_date': entry['commit']['committed_date'],
                },
                'lines': entry['lines'],
            }
            for entry in blame
        ]

    @mcp.tool
    def search_code(
        project_id: str,
        query: str,
        ref: str | None = None,
    ) -> list[dict]:
        project = client.get_project(project_id)
        params = {'scope': 'blobs', 'search': query}
        if ref:
            params['ref'] = ref

        results = project.search(**params)

        return [
            {
                'basename': r['basename'],
                'data': r['data'],
                'path': r['path'],
                'filename': r['filename'],
                'ref': r['ref'],
                'startline': r['startline'],
                'project_id': r['project_id'],
            }
            for r in results
        ]

    @mcp.tool
    def list_branches(
        project_id: str,
        search: str | None = None,
    ) -> list[dict]:
        project = client.get_project(project_id)
        params = {'iterator': True}
        if search:
            params['search'] = search

        branches = project.branches.list(**params)

        return [
            {
                'name': b.name,
                'merged': b.merged,
                'protected': b.protected,
                'default': b.default,
                'web_url': b.web_url,
                'commit': {
                    'id': b.commit['id'],
                    'short_id': b.commit['short_id'],
                    'title': b.commit['title'],
                    'author_name': b.commit['author_name'],
                    'committed_date': b.commit['committed_date'],
                },
            }
            for b in branches
        ]

    @mcp.tool
    def list_commits(
        project_id: str,
        ref_name: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        project = client.get_project(project_id)
        params = {'iterator': True}
        if ref_name:
            params['ref_name'] = ref_name
        if since:
            params['since'] = since
        if until:
            params['until'] = until

        commits = project.commits.list(**params)

        return [
            {
                'id': c.id,
                'short_id': c.short_id,
                'title': c.title,
                'message': c.message,
                'author_name': c.author_name,
                'author_email': c.author_email,
                'authored_date': c.authored_date,
                'committer_name': c.committer_name,
                'committed_date': c.committed_date,
                'web_url': c.web_url,
            }
            for c in commits
        ]

    @mcp.tool
    def get_commit(
        project_id: str,
        sha: str,
    ) -> dict:
        project = client.get_project(project_id)
        commit = project.commits.get(sha)

        return {
            'id': commit.id,
            'short_id': commit.short_id,
            'title': commit.title,
            'message': commit.message,
            'author_name': commit.author_name,
            'author_email': commit.author_email,
            'authored_date': commit.authored_date,
            'committer_name': commit.committer_name,
            'committed_date': commit.committed_date,
            'web_url': commit.web_url,
            'parent_ids': commit.parent_ids,
            'stats': commit.stats,
        }
