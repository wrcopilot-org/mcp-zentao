"""
ZenTao OpenAPI registry.

Centralizes endpoint definitions, pagination rules, and verification status.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """Endpoint specification.

    Args:
        name: Logical endpoint name.
        method: HTTP method, such as GET or POST.
        path: Endpoint path template without base URL.
        verified: Whether the endpoint has been verified.
        notes: Optional notes about usage or constraints.
    """

    name: str
    method: str
    path: str
    verified: bool
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class PaginationSpec:
    """Pagination URL specification."""

    base_endpoint: str
    operation: str
    template: str
    examples: tuple[str, ...]


PAGINATION_TEMPLATE = (
    "{base_endpoint}-{operation}-{sort_key}-{rec_total}-{rec_per_page}-{page_id}.json"
)

PAGINATION_SPECS: tuple[PaginationSpec, ...] = (
    PaginationSpec(
        base_endpoint="my-task",
        operation="assignedTo",
        template=PAGINATION_TEMPLATE,
        examples=(
            "my-task-assignedTo-id_desc-301-20-2.json",
        ),
    ),
    PaginationSpec(
        base_endpoint="my-bug",
        operation="assignedTo",
        template=PAGINATION_TEMPLATE,
        examples=(
            "my-bug-assignedTo-id_desc-305-20-2.json",
        ),
    ),
)

ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec(
        name="session.get_session_id",
        method="GET",
        path="/api-getSessionID.json",
        verified=True,
    ),
    EndpointSpec(
        name="session.login",
        method="GET",
        path="/user-login-{sessionid}.json",
        verified=True,
    ),
    EndpointSpec(
        name="session.logout",
        method="GET",
        path="/user-logout-{sessionid}.json",
        verified=True,
    ),
    EndpointSpec(
        name="user.list",
        method="GET",
        path="/company-browse-{dept_id}.json",
        verified=True,
    ),
    EndpointSpec(
        name="project.my_list",
        method="GET",
        path="/my-project.json",
        verified=True,
    ),
    EndpointSpec(
        name="project.task_list",
        method="GET",
        path="/project-task-{project_id}.json",
        verified=True,
    ),
    EndpointSpec(
        name="project.bug_list",
        method="GET",
        path="/project-bug-{project_id}.json",
        verified=True,
    ),
    EndpointSpec(
        name="task.my_list",
        method="GET",
        path="/my-task.json",
        verified=True,
    ),
    EndpointSpec(
        name="task.detail",
        method="GET",
        path="/task-view-{task_id}.json",
        verified=True,
    ),
    EndpointSpec(
        name="bug.my_list",
        method="GET",
        path="/my-bug.json",
        verified=True,
    ),
    EndpointSpec(
        name="bug.detail",
        method="GET",
        path="/bug-view-{bug_id}.json",
        verified=True,
    ),
    EndpointSpec(
        name="task.create",
        method="POST",
        path="/task-create-{project_id}--{module_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="task.start",
        method="POST",
        path="/task-start-{task_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="task.finish",
        method="POST",
        path="/task-finish-{task_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="task.close",
        method="POST",
        path="/task-close-{task_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="bug.create",
        method="POST",
        path="/bug-create-{product_id}-{branch}-moduleID={module_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="bug.resolve",
        method="POST",
        path="/bug-resolve-{bug_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="bug.confirm",
        method="POST",
        path="/bug-confirmBug-{bug_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="bug.close",
        method="POST",
        path="/bug-close-{bug_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="project.create",
        method="POST",
        path="/project-create-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="project.close",
        method="POST",
        path="/project-close-{project_id}-{sessionid}.json",
        verified=False,
    ),
    EndpointSpec(
        name="project.start",
        method="POST",
        path="/project-start-{project_id}-{sessionid}.json",
        verified=False,
    ),
)


def list_endpoints() -> list[EndpointSpec]:
    """Return all endpoint specifications.

    Returns:
        Endpoint specs in registration order.
    """

    return list(ENDPOINTS)


def list_verified_endpoints() -> list[EndpointSpec]:
    """Return verified endpoint specifications."""

    return [endpoint for endpoint in ENDPOINTS if endpoint.verified]


def list_unverified_endpoints() -> list[EndpointSpec]:
    """Return unverified endpoint specifications."""

    return [endpoint for endpoint in ENDPOINTS if not endpoint.verified]


def list_pagination_specs() -> list[PaginationSpec]:
    """Return pagination specifications."""

    return list(PAGINATION_SPECS)
