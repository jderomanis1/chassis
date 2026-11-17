import pytest

pytest.importorskip("starlette", reason="Install the portal extra for HTTP tests")
pytest.importorskip("uvicorn", reason="Install the portal extra for HTTP tests")

from starlette.testclient import TestClient
from .helpers import issue
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig


@pytest.fixture
def portal_config(git_repo):
    return PortalConfig(root=git_repo, viewer_token=issue(git_repo, "reviewer"))


@pytest.fixture
def client(portal_config):
    with TestClient(create_app(portal_config), base_url="http://127.0.0.1:8765") as client:
        yield client
