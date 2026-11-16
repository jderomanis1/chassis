"""Transport-independent write failures with machine-readable details."""


class WriteError(ValueError):
    code = "write_refused"

    def __init__(self, message: str, **details):
        super().__init__(message)
        self.details = details

    def as_dict(self) -> dict:
        return {"error": self.code, "message": str(self), **self.details}


class AuthorizationError(WriteError):
    code = "unauthorized"


class NotFoundError(WriteError):
    code = "not_found"


class ConflictError(WriteError):
    code = "conflict"

    def __init__(self, identifier: str, expected_version: int, current_version: int):
        super().__init__(f"{identifier}: expected version {expected_version}; "
                         f"current version {current_version}", id=identifier,
                         expected_version=expected_version, current_version=current_version)


class DirtyRecordError(WriteError):
    code = "dirty_record"


class GitError(WriteError):
    code = "git_error"


class CommittedIndexError(WriteError):
    code = "committed_index_error"
