"""Validated policy and exact venture/type authorization for configured callers."""

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from chassis.errors import AuthorizationError
from chassis.markdown import ParsedRecord, RecordFileError, UniqueKeyLoader
from chassis.models import RecordId, RecordType


class AgentPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ventures: dict[RecordId, dict[RecordType, Literal["read", "write"]]]


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    version: Annotated[int, Field(ge=1, le=1)]
    unknown_agent: Literal["read"]
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


def authorize_writer(root: Path, agent: str) -> Policy:
    """Policy read is required; deny unknown/read-only agents before record I/O."""
    try:
        policy = load_policy(root)
    except RecordFileError as exc:
        raise AuthorizationError(f"Writes denied: {exc}") from exc
    grants = policy.agents.get(agent)
    if grants is None or not any(grant == "write" for types in grants.ventures.values()
                                 for grant in types.values()):
        raise AuthorizationError(f"{agent}: no write grant", agent=agent)
    return policy


def require_grant(policy: Policy, agent: str, venture: str, record_type: str) -> None:
    grants = policy.agents.get(agent)
    if grants is None or grants.ventures.get(venture, {}).get(record_type) != "write":
        raise AuthorizationError(f"{agent}: no write grant for {venture}/{record_type}",
                                 agent=agent, venture=venture, type=record_type)
