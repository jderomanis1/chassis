"""Bounded HTTP edit proposals delegated to the existing record transaction."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, ValidationError, model_validator
from starlette.responses import JSONResponse
from starlette.routing import Route

from chassis.errors import AuthorizationError, ConflictError, DirtyRecordError, NotFoundError, WriteError
from chassis.markdown import RecordFileError
from chassis.git import Identity
from chassis.models import IsoDate, RecordId
from chassis.policy import authorize_reader, visible_records
from chassis.portal.write_guard import MAX_BODY
from chassis.store import RecordStore
from chassis.validation import read_vault

Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=4096)]


class Changes(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)] = None
    status: Literal["planned", "in_progress", "blocked", "done"] = None
    next_step: Text = None
    blocker_reason: Annotated[str, StringConstraints(max_length=4096)] | None = None
    due_at: IsoDate | None = None
    depends_on: Annotated[list[RecordId], Field(max_length=40)] | None = None

    @model_validator(mode="after")
    def nonempty(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one editable field")
        return self


class Edit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    changes: Changes
    expected_version: Annotated[int, Field(ge=1)]


CONFLICT_MESSAGE = ("This record changed before the save landed. Your edit was not saved. "
                    "Reload to see the latest version.")


def failure(code, message, status, **details):
    return JSONResponse({"error": {"code": code, "message": message, **details}}, status_code=status)


def viewer_record(config, identifier):
    """Visibility without a vault-wide graph check.

    The index refresh validates every dependency. A deleted hidden link would
    fail that check before the store can drop the id and save the edit.
    """
    policy = authorize_reader(config.root, config.viewer_agent, config.viewer_token)
    if policy is None:
        return None
    try:
        items = read_vault(config.root)
    except RecordFileError:
        return None
    rows = [item.record.model_dump(mode="json") | {"body": item.body} for item in items]
    return next((row for row in visible_records(rows, policy, config.viewer_agent)
                 if row["id"] == identifier), None)


def patch_record(request):
    config = request.app.state.config
    try:
        identifier = TypeAdapter(RecordId).validate_python(request.path_params["id"])
        edit = Edit.model_validate_json(request.state.payload)
        visible = viewer_record(config, identifier)
        if visible is None:
            raise NotFoundError("Not found")
        if len(visible["body"].encode()) > MAX_BODY:
            return failure("validation", "Record body exceeds the canvas edit limit", 400)
        store = RecordStore(config.root, token=config.editor_token,
                            identity=Identity(config.editor_agent, f"{config.editor_agent}@chassis.local"),
                            normal_only=True)
        result = store.update_record(identifier, edit.changes.model_dump(mode="json", exclude_unset=True),
                                     edit.expected_version, config.editor_agent)
        return JSONResponse({"record": {key: result["record"][key] for key in ("id", "version")},
                             "commit": result["commit"]})
    except (AuthorizationError, NotFoundError):
        return failure("not_found", "Not found", 404)
    except ConflictError as exc:
        return failure("conflict", CONFLICT_MESSAGE, 409,
                       current_version=exc.details["current_version"])
    except DirtyRecordError as exc:
        return failure("dirty_record", str(exc), 409)
    except ValidationError as exc:
        issue = exc.errors(include_input=False, include_context=False)[0]
        # A repeated id is a validation failure. The body stays the generic envelope.
        if "duplicate" in issue.get("msg", "").casefold():
            return failure("validation", "Record update could not be completed", 400)
        field = ".".join(map(str, issue["loc"]))
        return failure("validation", f"{field}: {issue['msg']}" if field else issue["msg"], 400)
    except RecordFileError as exc:
        reason = str(exc).split(": ", 1)[-1]
        if "/" in reason or "\\" in reason:
            reason = "Record update could not be completed"
        return failure("validation", reason, 400)
    except WriteError as exc:
        if str(exc) == "invalid dependency":
            return failure("validation", "invalid dependency", 400)
        recovery = {k: v for k, v in exc.details.items()
                    if k in {"committed", "commit", "current_version", "commit_state"}}
        if recovery:
            return failure(exc.code, "Save needs recovery. Reload before trying again.", 500, **recovery)
        return failure("validation", "Record update could not be completed", 400)


routes = [Route("/api/records/{id:path}", patch_record, methods=["PATCH"])]
