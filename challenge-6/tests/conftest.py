"""Pytest fixtures for deployed ReadyNow integration tests."""

from __future__ import annotations

import os
import pathlib
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def project_id() -> str:
    value = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    if not value:
        pytest.skip("GOOGLE_CLOUD_PROJECT is not set.")
    return value


@pytest.fixture(scope="session")
def location() -> str:
    return os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1").strip() or "us-central1"


@pytest.fixture(scope="session")
def deployed_resource_name() -> str:
    value = os.getenv("AGENT_ENGINE_RESOURCE_NAME", "").strip()
    if not value:
        pytest.skip("AGENT_ENGINE_RESOURCE_NAME is not set.")
    return value


@pytest.fixture(scope="session")
def remote_client_module():
    pytest.importorskip("vertexai")
    from lib import remote_client

    return remote_client


@pytest.fixture(scope="session")
def remote_agent(project_id: str, location: str, deployed_resource_name: str, remote_client_module):
    """Return the deployed agent object referenced by AGENT_ENGINE_RESOURCE_NAME."""
    return remote_client_module.get_remote_agent(
        resource_name=deployed_resource_name,
        project_id=project_id,
        location=location,
    )
