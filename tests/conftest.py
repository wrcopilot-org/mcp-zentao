"""
Pytest configuration for ZenTao API tests.

Provides fixtures for schemathesis-based API testing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from dotenv import load_dotenv

if TYPE_CHECKING:
    from collections.abc import Generator

# Load .env file from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--zentao-url",
        action="store",
        default=os.environ.get("ZENTAO_URL", "http://localhost"),
        help="ZenTao server base URL",
    )
    parser.addoption(
        "--zentao-account",
        action="store",
        default=os.environ.get("ZENTAO_ACCOUNT", "admin"),
        help="ZenTao login account",
    )
    parser.addoption(
        "--zentao-password",
        action="store",
        default=os.environ.get("ZENTAO_PASSWORD", ""),
        help="ZenTao login password",
    )


@pytest.fixture(scope="session")
def zentao_url(request: pytest.FixtureRequest) -> str:
    """Get ZenTao server URL from command line or environment."""
    url = request.config.getoption("--zentao-url")
    # Ensure URL doesn't end with slash for consistent path joining
    return url.rstrip("/")


@pytest.fixture(scope="session")
def zentao_account(request: pytest.FixtureRequest) -> str:
    """Get ZenTao account from command line or environment."""
    return request.config.getoption("--zentao-account")


@pytest.fixture(scope="session")
def zentao_password(request: pytest.FixtureRequest) -> str:
    """Get ZenTao password from command line or environment."""
    return request.config.getoption("--zentao-password")


@pytest.fixture(scope="session")
def openapi_path() -> str:
    """Path to OpenAPI specification file."""
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "docs",
        "openapi",
        "zentao-api.yaml",
    )
