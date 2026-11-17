"""Validated policy and exact venture/type authorization for configured callers."""

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from chassis.errors import AuthorizationError
from chassis.markdown import ParsedRecord, RecordFileError, UniqueKeyLoader
from chassis.models import RecordId, RecordType
from chassis.identity import authenticate


class AgentPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ventures: dict[RecordId, dict[RecordType, Literal["read", "write"]]]
    clearance: Literal["normal", "restricted"] = "normal"


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    version: Annotated[int, Field(ge=1, le=1)]
    unknown_agent: Literal["deny"] = "deny"
    agents: dict[RecordId, AgentPolicy]


def load_policy(root: Path) -> Policy:
    path = root / "agents.yaml"
    try:
        fields = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        return Policy.model_validate(fields)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise RecordFileError(f"{path.as_posix()}: {exc}") from exc


def validate_policy_references(root: Path, policy: Policy, records: dict[str, ParsedRecord]) -> None:
    for agent, grants in policy.agents.items():
        for venture in grants.ventures:
            item = records.get(venture)
            if item is None or item.record.type != "venture":
                raise RecordFileError(
                    f"{root / 'agents.yaml'}: agent {agent!r} venture {venture!r} "
                    "must reference an existing venture")


def authorize_reader(root: Path, agent: str, token=None) -> Policy | None:
    try:
        policy = load_policy(root)
    except RecordFileError:
        return None
    return policy if agent in policy.agents and authenticate(root, agent, token) else None


def can_read_record(record, policy, agent):
    grants = policy.agents.get(agent)
    return grants is not None and grants.ventures.get(record["venture"], {}).get(record["type"]) in {"read", "write"} and (
        record["sensitivity"] != "restricted" or grants.clearance == "restricted")


def visible_records(records, policy, agent):
    visible = {r["id"]: r for r in records if can_read_record(r, policy, agent)}
    # Hiding an ancestor also hides descendants; no dangling identifying relations.
    while hidden := [key for key, r in visible.items() if r["venture"] not in visible
                     or (r["parent"] is not None and r["parent"] not in visible)]:
        for key in hidden:
            del visible[key]
    return [r | {"depends_on": [key for key in r["depends_on"] if key in visible]}
            for r in visible.values()]


def authorize_writer(root: Path, agent: str, token=None) -> Policy:
    """Policy read is required; deny unknown/read-only agents before record I/O."""
    try:
        policy = load_policy(root)
    except RecordFileError as exc:
        raise AuthorizationError("Write not permitted") from exc
    grants = policy.agents.get(agent)
    if grants is None or not any(grant == "write" for types in grants.ventures.values()
                                 for grant in types.values()):
        raise AuthorizationError("Write not permitted")
    if not authenticate(root, agent, token):
        raise AuthorizationError("Write not permitted")
    return policy


def require_grant(policy: Policy, agent: str, venture: str, record_type: str) -> None:
    grants = policy.agents.get(agent)
    if grants is None or grants.ventures.get(venture, {}).get(record_type) != "write":
        raise AuthorizationError("Write not permitted")


def require_clearance(policy, agent, sensitivity):
    if sensitivity == "restricted" and policy.agents[agent].clearance != "restricted":
        raise AuthorizationError("Write not permitted")
