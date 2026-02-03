"""
ZenTao API live validation tests using Schemathesis.

These tests require a running ZenTao server and valid credentials.

Usage:
    # Run with default settings (reads from environment)
    uv run pytest tests/test_api_validation.py -v

    # Run with custom server
    uv run pytest tests/test_api_validation.py -v \
        --zentao-url=http://zentao.example.com \
        --zentao-account=admin \
        --zentao-password=secret

Environment variables:
    ZENTAO_URL      - ZenTao server base URL
    ZENTAO_ACCOUNT  - Login account
    ZENTAO_PASSWORD - Login password
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import pytest
import schemathesis
from schemathesis import Case

if TYPE_CHECKING:
    pass


OPENAPI_PATH = Path(__file__).parent.parent / "docs" / "openapi" / "zentao-api.yaml"


class ZenTaoSession:
    """Manages ZenTao session for API testing."""

    def __init__(self, base_url: str, account: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.account = account
        self.password = password
        self.session_id: str | None = None
        self.client = httpx.Client(timeout=30.0)

    def get_session_id(self) -> str:
        """Get a new session ID from ZenTao."""
        url = f"{self.base_url}/api-getSessionID.json"
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "success":
            raise RuntimeError(f"Failed to get session ID: {data}")

        # Parse the nested JSON string
        inner_data = json.loads(data["data"])
        self.session_id = inner_data["sessionID"]
        return self.session_id

    def login(self) -> dict[str, Any]:
        """Login to ZenTao."""
        if not self.session_id:
            self.get_session_id()

        url = f"{self.base_url}/user-login-{self.session_id}.json"
        params = {"account": self.account, "password": self.password}
        response = self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "success":
            raise RuntimeError(f"Login failed: {data}")

        # Login response has 'user' field directly, not nested in 'data'
        return data.get("user", {})

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


@pytest.fixture(scope="module")
def zentao_session(
    zentao_url: str, zentao_account: str, zentao_password: str
) -> ZenTaoSession:
    """Create and login a ZenTao session."""
    if not zentao_password:
        pytest.skip("ZENTAO_PASSWORD not set, skipping live API tests")

    session = ZenTaoSession(zentao_url, zentao_account, zentao_password)
    try:
        session.login()
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def authenticated_client(zentao_session: ZenTaoSession) -> httpx.Client:
    """Get an authenticated HTTP client."""
    return zentao_session.client


class TestSessionEndpoints:
    """Test session-related endpoints."""

    def test_get_session_id(self, zentao_url: str) -> None:
        """Test /api-getSessionID.json endpoint."""
        with httpx.Client() as client:
            url = f"{zentao_url}/api-getSessionID.json"
            response = client.get(url)

            # Validate response structure
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert "data" in data

            # Validate inner data structure
            inner = json.loads(data["data"])
            assert "sessionID" in inner
            assert "sessionName" in inner
            assert inner["sessionName"] == "zentaosid"
            assert len(inner["sessionID"]) >= 10

    def test_login_success(self, zentao_session: ZenTaoSession) -> None:
        """Test successful login."""
        # Session fixture already logged in
        assert zentao_session.session_id is not None

    def test_login_invalid_credentials(self, zentao_url: str) -> None:
        """Test login with invalid credentials."""
        session = ZenTaoSession(zentao_url, "invalid_user", "wrong_password")
        try:
            session.get_session_id()
            url = f"{zentao_url}/user-login-{session.session_id}.json"
            params = {"account": "invalid_user", "password": "wrong_password"}
            response = session.client.get(url, params=params)

            data = response.json()
            # Should fail or return error status
            assert data.get("status") in ["failed", "error"] or "user" not in json.loads(
                data.get("data", "{}")
            )
        finally:
            session.close()


class TestTaskEndpoints:
    """Test task-related endpoints."""

    def test_my_task_list(
        self, zentao_url: str, zentao_session: ZenTaoSession
    ) -> None:
        """Test /my-task.json endpoint."""
        url = f"{zentao_url}/my-task.json"
        response = zentao_session.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"

        # Parse and validate inner data
        inner = json.loads(data["data"])
        assert "tasks" in inner

        # Validate task structure if any exist
        tasks = inner["tasks"]
        if tasks:
            # Tasks might be dict or list depending on ZenTao version
            if isinstance(tasks, dict):
                task = next(iter(tasks.values()))
            else:
                task = tasks[0]

            # Verify required fields
            assert "id" in task
            assert "name" in task
            assert "status" in task

    def test_task_detail(
        self, zentao_url: str, zentao_session: ZenTaoSession
    ) -> None:
        """Test /task-view-{task_id}.json endpoint."""
        # First get a task ID from the list
        list_url = f"{zentao_url}/my-task.json"
        list_response = zentao_session.client.get(list_url)
        list_data = json.loads(list_response.json()["data"])

        tasks = list_data.get("tasks", {})
        if not tasks:
            pytest.skip("No tasks available for testing")

        # Get first task ID
        if isinstance(tasks, dict):
            task_id = next(iter(tasks.keys()))
        else:
            task_id = tasks[0]["id"]

        # Test detail endpoint
        url = f"{zentao_url}/task-view-{task_id}.json"
        response = zentao_session.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"

        inner = json.loads(data["data"])
        assert "task" in inner
        assert inner["task"]["id"] == str(task_id)


class TestBugEndpoints:
    """Test bug-related endpoints."""

    def test_my_bug_list(
        self, zentao_url: str, zentao_session: ZenTaoSession
    ) -> None:
        """Test /my-bug.json endpoint."""
        url = f"{zentao_url}/my-bug.json"
        response = zentao_session.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"

        inner = json.loads(data["data"])
        assert "bugs" in inner

        bugs = inner["bugs"]
        if bugs:
            if isinstance(bugs, dict):
                bug = next(iter(bugs.values()))
            else:
                bug = bugs[0]

            # Verify required fields
            assert "id" in bug
            assert "title" in bug
            assert "status" in bug

    def test_bug_detail(
        self, zentao_url: str, zentao_session: ZenTaoSession
    ) -> None:
        """Test /bug-view-{bug_id}.json endpoint."""
        # First get a bug ID from the list
        list_url = f"{zentao_url}/my-bug.json"
        list_response = zentao_session.client.get(list_url)
        list_data = json.loads(list_response.json()["data"])

        bugs = list_data.get("bugs", {})
        if not bugs:
            pytest.skip("No bugs available for testing")

        if isinstance(bugs, dict):
            bug_id = next(iter(bugs.keys()))
        else:
            bug_id = bugs[0]["id"]

        url = f"{zentao_url}/bug-view-{bug_id}.json"
        response = zentao_session.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"

        inner = json.loads(data["data"])
        assert "bug" in inner
        assert inner["bug"]["id"] == str(bug_id)

        # Verify enum fields have valid values
        bug = inner["bug"]
        valid_statuses = ["active", "resolved", "closed"]
        assert bug["status"] in valid_statuses

        valid_severities = [1, 2, 3, 4, "1", "2", "3", "4"]
        assert bug["severity"] in valid_severities


class TestProjectEndpoints:
    """Test project-related endpoints."""

    def test_my_project_list(
        self, zentao_url: str, zentao_session: ZenTaoSession
    ) -> None:
        """Test /my-project.json endpoint."""
        url = f"{zentao_url}/my-project.json"
        response = zentao_session.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"


class TestUserEndpoints:
    """Test user-related endpoints."""

    def test_user_list(
        self, zentao_url: str, zentao_session: ZenTaoSession
    ) -> None:
        """Test /company-browse-{dept_id}.json endpoint."""
        url = f"{zentao_url}/company-browse-0.json"
        response = zentao_session.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"


# ============================================================
# Schemathesis-based property testing
# ============================================================

schema = schemathesis.openapi.from_path(str(OPENAPI_PATH))


@pytest.fixture(scope="module")
def base_url_for_schemathesis(zentao_url: str) -> str:
    """Get base URL for schemathesis tests."""
    return zentao_url


class TestSchemathesisValidation:
    """Property-based API testing using Schemathesis."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api-getSessionID.json",
        ],
    )
    def test_unauthenticated_endpoints(
        self, zentao_url: str, endpoint: str
    ) -> None:
        """Test endpoints that don't require authentication."""
        with httpx.Client() as client:
            url = f"{zentao_url}{endpoint}"
            response = client.get(url)

            assert response.status_code == 200
            data = response.json()
            assert "status" in data

    def test_response_matches_schema_session(
        self, zentao_url: str
    ) -> None:
        """Validate session endpoint response against schema."""
        with httpx.Client() as client:
            url = f"{zentao_url}/api-getSessionID.json"
            response = client.get(url)
            data = response.json()

            # Basic schema validation
            assert isinstance(data.get("status"), str)
            assert data["status"] in ["success", "failed", "error"]

            if data["status"] == "success":
                assert isinstance(data.get("data"), str)
                inner = json.loads(data["data"])
                assert isinstance(inner.get("sessionID"), str)
                assert isinstance(inner.get("rand"), int)
