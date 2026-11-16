"""Local per-agent bearer credentials. Only SHA-256 digests are persisted."""
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, StringConstraints, TypeAdapter

from chassis.atomic import vault_lock, write_atomic
from chassis.markdown import UniqueKeyLoader
from chassis.models import RecordId


class TokenFile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1]
    tokens: dict[RecordId, Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]]


def caller_id(agent=None):
    return os.environ.get("CHASSIS_AGENT_ID", "").strip() if agent is None else agent


def _token_path(root):
    path = Path(root) / ".chassis/agent-tokens.yaml"
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("Credential paths cannot be symlinks")
    return path


def authenticate(root, agent, token=None):
    token = os.environ.get("CHASSIS_AGENT_TOKEN", "") if token is None else token
    if not isinstance(agent, str) or not agent or not isinstance(token, str) or not token:
        return False
    try:
        data = TokenFile.model_validate(yaml.load(_token_path(root).read_text(), Loader=UniqueKeyLoader))
        digest = hashlib.sha256(token.encode()).hexdigest()
        return hmac.compare_digest(data.tokens.get(agent, ""), digest)
    except (OSError, ValueError, yaml.YAMLError):
        return False


def create_agent_token(root, agent):
    """Local operator command: rotate one credential, returning the secret once."""
    from chassis.policy import load_policy

    root = Path(root).resolve()
    TypeAdapter(RecordId).validate_python(agent)
    if agent not in load_policy(root).agents:
        raise ValueError("Agent must exist in agents.yaml before creating a token")
    with vault_lock(root):
        path = _token_path(root)
        try:
            data = TokenFile.model_validate(yaml.load(path.read_text(), Loader=UniqueKeyLoader)) if path.exists() else TokenFile(version=1, tokens={})
        except (ValueError, OSError, yaml.YAMLError) as exc:
            raise ValueError("Credential store invalid") from exc
        token = secrets.token_urlsafe(32)
        data.tokens[agent] = hashlib.sha256(token.encode()).hexdigest()
        write_atomic(path, yaml.safe_dump(data.model_dump()).encode())
        path.chmod(0o600)
    return token
