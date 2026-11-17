"""Transport-neutral tool contracts and thin calls into the CLI's library paths."""

import logging
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chassis.errors import NotFoundError, WriteError
from chassis.audit import record_event
from chassis.index import IndexFileError, RecordIndex
from chassis.models import RecordId, RecordType
from chassis.store import RecordStore

logger = logging.getLogger(__name__)


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ListArguments(Arguments):
    filters: dict[str, str | None] | None = None


class ReadArguments(Arguments):
    id: RecordId


class SearchArguments(Arguments):
    query: str


class CreateArguments(Arguments):
    type: RecordType
    fields: dict[str, Any]


class TemplateArguments(Arguments):
    template: Literal["initiative", "agent"]
    venture: RecordId
    fields: dict[str, Any]


class UpdateArguments(ReadArguments):
    changes: dict[str, Any]
    expected_version: Annotated[int, Field(ge=1)]


TOOL_INPUTS = {"list_records": ListArguments, "read_record": ReadArguments,
               "search": SearchArguments, "create_record": CreateArguments,
               "create_from_template": TemplateArguments, "update_record": UpdateArguments}


def validation_error(exc: ValueError, fallback: str) -> dict:
    cause = exc
    while cause is not None:
        if isinstance(cause, ValidationError):
            issues = [{"field": ".".join(map(str, item["loc"])) or fallback,
                       "reason": item["msg"]} for item in cause.errors(
                           include_input=False, include_context=False, include_url=False)]
            return {"error": "validation", **issues[0], "issues": issues}
        cause = cause.__cause__
    details = exc.details if isinstance(exc, WriteError) else {}
    field = details.get("field") or ", ".join(details.get("fields", [])) or fallback
    return {**details, "error": "validation", "field": field, "reason": details.get("reason", str(exc))}


class ToolHandlers:
    """One trusted caller configuration; model-supplied metadata cannot replace it."""

    def __init__(self, root: Path, agent: str, token=None):
        self.index, self.store = RecordIndex(root, agent=agent, token=token), RecordStore(root, token=token)
        self.agent = agent

    def call(self, name: str, arguments: dict | None) -> dict:
        if name not in TOOL_INPUTS:
            return {"error": "not_found", "reason": "Unknown tool", "tool": name}
        try:
            args = TOOL_INPUTS[name].model_validate({} if arguments is None else arguments)
        except ValidationError as exc:
            try:
                record_event(self.index.root, self.agent, name, "validation")
            except WriteError as failure:
                return failure.as_dict()
            return validation_error(exc, "arguments")
        logger.info("Calling %s", name)
        try:
            return self._call(name, args)
        except WriteError as exc:
            if exc.code in {"git_error", "committed_index_error"}:
                # Hooks and storage failures can contain arbitrary diagnostics.
                # Keep recovery facts, including successful/uncertain commits.
                logger.error("%s: %s", exc.code, exc)
                return {**exc.details, "error": exc.code,
                        "reason": "Git or index operation failed; inspect server stderr before retrying."}
            if exc.code != "write_refused":
                return exc.as_dict()
            return validation_error(exc, "record")
        except IndexFileError:
            logger.error("Index operation failed")
            return {"error": "internal_error", "reason": "Operation failed; inspect server stderr before retrying."}
        except ValueError as exc:
            return validation_error(exc, "filters" if name == "list_records" else "record")
        except Exception:
            logger.exception("Tool %s failed", name)
            return {"error": "internal_error", "reason": "Operation failed; inspect server stderr before retrying."}

    def _call(self, name: str, args: Arguments) -> dict:
        if name == "list_records":
            return {"records": self.index.list_records(args.filters)}
        if name == "read_record":
            record = self.index.get_record(args.id)
            if record is None:
                raise NotFoundError("Record not found")
            return {"record": record}
        if name == "search":
            return {"records": self.index.search(args.query)}
        if name == "create_record":
            return self.store.create_record(args.type, args.fields, self.agent)
        if name == "create_from_template":
            return self.store.create_from_template(args.template, args.venture, args.fields, self.agent)
        return self.store.update_record(args.id, args.changes, args.expected_version, self.agent)
