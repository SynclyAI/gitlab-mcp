from pydantic import BaseModel, ConfigDict, field_validator


class MergeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    iid: int
    title: str
    state: str
    author: str
    source_branch: str
    target_branch: str
    web_url: str
    created_at: str
    updated_at: str
    user_notes_count: int

    @field_validator('author', mode='before')
    @classmethod
    def extract_author(cls, v):
        if isinstance(v, dict):
            return v['username']

        return v


class MergeRequestDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    iid: int
    title: str
    description: str | None
    state: str
    author: str
    source_branch: str
    target_branch: str
    web_url: str
    created_at: str
    updated_at: str
    merged_by: str | None
    merged_at: str | None
    labels: list[str]
    milestone: str | None
    assignees: list[str]
    reviewers: list[str]
    draft: bool
    work_in_progress: bool
    has_conflicts: bool
    blocking_discussions_resolved: bool

    @field_validator('author', mode='before')
    @classmethod
    def extract_author(cls, v):
        if isinstance(v, dict):
            return v['username']

        return v

    @field_validator('merged_by', mode='before')
    @classmethod
    def extract_merged_by(cls, v):
        if isinstance(v, dict):
            return v['username']

        return v

    @field_validator('milestone', mode='before')
    @classmethod
    def extract_milestone(cls, v):
        if isinstance(v, dict):
            return v['title']

        return v

    @field_validator('assignees', mode='before')
    @classmethod
    def extract_assignees(cls, v):
        if v and isinstance(v[0], dict):
            return [a['username'] for a in v]

        return v

    @field_validator('reviewers', mode='before')
    @classmethod
    def extract_reviewers(cls, v):
        if v and isinstance(v[0], dict):
            return [r['username'] for r in v]

        return v


class MergeRequestChange(BaseModel):
    old_path: str
    new_path: str
    a_mode: str
    b_mode: str
    new_file: bool
    renamed_file: bool
    deleted_file: bool
    diff: str


class MergeRequestChanges(BaseModel):
    changes: list[MergeRequestChange]


class Commit(BaseModel):
    id: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    authored_date: str
    committed_date: str


class CommitDetails(Commit):
    model_config = ConfigDict(from_attributes=True)

    committer_name: str
    web_url: str
    parent_ids: list[str] | None = None
    stats: dict | None = None


class Pipeline(BaseModel):
    id: int
    sha: str
    ref: str
    status: str
    web_url: str
    created_at: str
    updated_at: str


class Note(BaseModel):
    id: int
    body: str
    author: str
    created_at: str
    updated_at: str | None = None
    system: bool | None = None
    resolvable: bool | None = None
    resolved: bool = False
    position: dict | None = None

    @field_validator('author', mode='before')
    @classmethod
    def extract_author(cls, v):
        if isinstance(v, dict):
            return v['username']

        return v


class Discussion(BaseModel):
    id: str
    individual_note: bool
    notes: list[Note]


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    path_with_namespace: str
    web_url: str
    description: str | None


class TreeItem(BaseModel):
    id: str
    name: str
    type: str
    path: str
    mode: str


class FileContent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_path: str
    file_name: str
    size: int
    encoding: str
    content: str
    ref: str
    last_commit_id: str


class BlameCommit(BaseModel):
    id: str
    author_name: str
    author_email: str
    message: str
    committed_date: str


class BlameEntry(BaseModel):
    commit: BlameCommit
    lines: list[str]


class CodeSearchResult(BaseModel):
    basename: str
    data: str
    path: str
    filename: str
    ref: str
    startline: int
    project_id: int


class BranchCommit(BaseModel):
    id: str
    short_id: str
    title: str
    author_name: str
    committed_date: str


class Branch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    merged: bool
    protected: bool
    default: bool
    web_url: str
    commit: BranchCommit

    @field_validator('commit', mode='before')
    @classmethod
    def parse_commit(cls, v):
        if isinstance(v, dict):
            return BranchCommit(**v)

        return v


class CommitListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ActionResult(BaseModel):
    status: str
    mr_iid: int
