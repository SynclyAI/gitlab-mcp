# GitLab On-Prem MCP Server Implementation Plan

## Technology Stack

- **Language:** Python 3.10+
- **GitLab API:** python-gitlab==7.0.0
- **MCP SDK:** fastmcp==2.14.1
- **Testing:** pytest>=8.0 (dev)

## Project Structure

```
gitlab-mcp/
├── pyproject.toml
├── Dockerfile
├── .gitignore
├── gitlab_mcp/
│   ├── __init__.py
│   ├── server.py              # FastMCP server entry point
│   ├── config.py              # Configuration from file/env
│   ├── auth.py                # OAuth + permission check logic
│   ├── client.py              # GitLab client wrapper
│   └── tools/
│       ├── __init__.py
│       ├── merge_requests.py  # MR tools
│       └── repository.py      # Repository tools
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_merge_requests.py
    └── test_repository.py
```

## Security Models Analysis

### Model A: Server-side Token (Current Plan)
Single GitLab token configured on server.

| Aspect | Impact |
|--------|--------|
| Authentication | None - anyone with MCP access can use it |
| Authorization | AI has access to all repos the token owner has |
| Audit trail | All actions logged under single GitLab user |
| Complexity | Low |
| Use case | Internal/trusted environments |

### Model B: User OAuth + User Token
Users authenticate via GitLab OAuth, their token used for API calls.

| Aspect | Impact |
|--------|--------|
| Authentication | GitLab OAuth - only authenticated users |
| Authorization | AI has same access as logged-in user |
| Audit trail | Actions logged under actual user |
| Complexity | Medium |
| Use case | Full user permission delegation to AI |

### Model C: User OAuth + Dedicated Service Token
Users authenticate via OAuth (gatekeeper), but API uses dedicated 'claude' service account.

| Aspect | Impact |
|--------|--------|
| Authentication | GitLab OAuth - only authenticated users |
| Authorization | AI limited to 'claude' user's repos (subset) |
| Audit trail | Actions logged under 'claude' user |
| Complexity | High |
| Use case | Restrict AI to specific repos regardless of user permissions |

### Model D: User OAuth + Intersection ✓ Selected
Users authenticate via OAuth, API uses intersection of user's and service account's permissions.

| Aspect | Impact |
|--------|--------|
| Authentication | GitLab OAuth - only authenticated users |
| Authorization | AI limited to repos both user AND service account can access |
| Audit trail | Service token (all AI actions under 'claude' user) |
| Complexity | High |
| Use case | Maximum restriction - user must have access AND repo must be AI-enabled |

#### OAuth Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Claude CLI │     │  MCP Server │     │   GitLab    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │ 1. Connect        │                   │
       │──────────────────>│                   │
       │                   │                   │
       │ 2. Auth required  │                   │
       │<──────────────────│                   │
       │                   │                   │
       │ 3. Browser: /oauth/authorize          │
       │───────────────────────────────────────>
       │                   │                   │
       │                   │ 4. Callback+code  │
       │                   │<──────────────────│
       │                   │                   │
       │                   │ 5. POST /oauth/token
       │                   │──────────────────>│
       │                   │   (user token)    │
       │                   │<──────────────────│
       │                   │                   │
       │ 6. Authenticated  │                   │
       │<──────────────────│                   │
       │                   │                   │
       │ 7. Tool call      │                   │
       │──────────────────>│ 8. Check access:  │
       │                   │    user token +   │
       │                   │    service token  │
       │                   │──────────────────>│
       │                   │                   │
       │                   │ 9. API call with  │
       │                   │    service token  │
       │                   │──────────────────>│
       │ 10. Result        │<──────────────────│
       │<──────────────────│                   │
```

#### GitLab OAuth Application Setup

Create in GitLab Admin → Applications:
- **Redirect URI:** `http://localhost:<port>/callback`
- **Scopes:** `read_user`, `read_api`, `read_repository`
- **Confidential:** Yes

#### Permission Check Logic (step 8)

```python
def check_access(project_id, user_token, service_token):
    # 1. Verify user can access project
    user_access = gitlab_api(user_token).project(project_id)
    if not user_access:
        raise PermissionDenied('User cannot access this project')

    # 2. Verify service account can access project
    service_access = gitlab_api(service_token).project(project_id)
    if not service_access:
        raise PermissionDenied('AI not enabled for this project')

    # 3. Use service token for actual operation
    return service_token
```

---

## Configuration

**Environment variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `GITLAB_URL` | yes | GitLab instance URL |
| `GITLAB_CA_CERT_PATH` | no | Path to CA certificate for self-signed certs |
| `GITLAB_SECRETS_PATH` | no | Path to secrets JSON file (default: `/run/secrets/gitlab.json`) |

**Secrets file** (`/run/secrets/gitlab.json`):
```json
{
  "oauth_client_id": "...",
  "oauth_client_secret": "...",
  "service_token": "glpat-xxxx"
}
```

| Field | Description |
|-------|-------------|
| `oauth_client_id` | GitLab OAuth application ID |
| `oauth_client_secret` | GitLab OAuth application secret |
| `service_token` | 'claude' service account PAT for API calls |

## MCP Tools

### Merge Request Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_merge_requests` | List MRs with filters | `project_id`, `state?`, `author_username?`, `assignee_username?` |
| `get_merge_request` | Get MR details | `project_id`, `mr_iid` |
| `get_merge_request_changes` | Get diff | `project_id`, `mr_iid` |
| `get_mr_commits` | List commits in MR | `project_id`, `mr_iid` |
| `get_mr_pipelines` | Get CI pipeline status | `project_id`, `mr_iid` |
| `get_mr_discussions` | Get review comments/threads | `project_id`, `mr_iid` |
| `add_mr_discussion` | Add inline comment on diff | `project_id`, `mr_iid`, `body`, `position` |
| `add_merge_request_comment` | Add general comment | `project_id`, `mr_iid`, `body` |
| `create_merge_request` | Create new MR | `project_id`, `source_branch`, `target_branch`, `title`, `description?` |
| `approve_merge_request` | Approve MR | `project_id`, `mr_iid` |
| `unapprove_merge_request` | Remove approval | `project_id`, `mr_iid` |
| `merge_merge_request` | Merge MR | `project_id`, `mr_iid`, `should_remove_source_branch?` |

### Repository Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_projects` | List accessible projects | `search?`, `owned?`, `membership?` |
| `get_repository_tree` | Browse files/directories | `project_id`, `path?`, `ref?`, `recursive?` |
| `get_file_content` | Get file content | `project_id`, `file_path`, `ref?` |
| `get_file_blame` | Get line-by-line authorship | `project_id`, `file_path`, `ref?` |
| `search_code` | Search code in project | `project_id`, `query`, `ref?` |
| `list_branches` | List branches | `project_id`, `search?` |
| `list_commits` | List commits | `project_id`, `ref_name?`, `since?`, `until?` |
| `get_commit` | Get commit details | `project_id`, `sha` |

## Implementation Phases

### Phase 1: Foundation
1. Create `pyproject.toml` with dependencies
2. Implement `config.py` - configuration from file/env
3. Implement `client.py` - GitLab client wrapper
4. Create `server.py` with FastMCP initialization

### Phase 2: Authentication
1. Implement `auth.py` - GitLab OAuthProxy integration
2. Add permission check logic (user ∩ service account)
3. Integrate auth with FastMCP server

### Phase 3: Repository Tools
1. `list_projects`
2. `get_repository_tree`
3. `get_file_content`
4. `get_file_blame`
5. `search_code`
6. `list_branches`
7. `list_commits`
8. `get_commit`

### Phase 4: Merge Request Tools
1. `list_merge_requests`
2. `get_merge_request`
3. `get_merge_request_changes`
4. `get_mr_commits`
5. `get_mr_pipelines`
6. `get_mr_discussions`
7. `add_mr_discussion`
8. `add_merge_request_comment`
9. `create_merge_request`
10. `approve_merge_request` / `unapprove_merge_request`
11. `merge_merge_request`

### Phase 5: Docker
1. Create Dockerfile

### Phase 6: Testing
1. Unit tests with mocked GitLab client

