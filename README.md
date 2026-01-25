# GitLab MCP Server

MCP (Model Context Protocol) server for AI-assisted code review with GitLab on-premise instances.

## Features

### Merge Request Tools
- List, get, create merge requests
- Get MR changes, commits, pipelines
- Get and add discussions/comments
- Approve, unapprove, merge MRs

### Repository Tools
- List projects
- Browse repository tree
- Get file content and blame
- Search code
- List branches and commits

## Security Model

Uses OAuth with intersection-based access control:
- User authenticates via GitLab OAuth
- AI access limited to repos both user AND service account can access
- All API calls made with service account token for audit trail

## Prerequisites

- Python 3.10+
- GitLab instance with OAuth application configured
- SSL certificate for HTTPS

## Setup

### 1. GitLab OAuth Application

Create in GitLab Admin > Applications:
- **Redirect URI:** `https://<server-host>:<port>/oauth/callback`
- **Scopes:** `read_user`, `read_api`, `read_repository`, `api` (for write operations)
- **Confidential:** Yes

### 2. Secrets File

Create a JSON file with credentials:

```json
{
  "oauth_client_id": "<gitlab-oauth-app-id>",
  "oauth_client_secret": "<gitlab-oauth-app-secret>",
  "service_token": "<service-account-personal-access-token>"
}
```

### 3. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITLAB_URL` | yes | GitLab instance URL |
| `GITLAB_SECRETS_PATH` | yes | Path to secrets JSON file |
| `MCP_SERVER_BASE_URL` | yes | Server URL with https and port (e.g., `https://localhost:8443`) |
| `MCP_SSL_CERT_PATH` | yes | Path to SSL certificate |
| `MCP_SSL_KEY_PATH` | yes | Path to SSL private key |
| `SSL_CERT_FILE` | no | CA certificate for GitLab (self-signed certs) |

### 4. Install

```bash
pip install .
```

## Running

```bash
gitlab-mcp
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
