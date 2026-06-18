DANGEROUS_PATHS = {
    "/tools/execute",
    "/terminal/execute",
    "/shell/execute",
}

DANGEROUS_SUFFIXES = {
    "/execute",
}

ALLOWED_STUB_PATHS = {
    "/tools/execution-stub",
    "/model-router/stub-test",
}

FORBIDDEN_ROUTE_PREFIXES = {
    "/oauth",
    "/payment",
    "/custom-webhook",
    "/user-supplied-webhook",
}

ALLOWED_RUNTIME_PATHS = {
    "/runtime/capabilities",
    "/runtime/readiness",
    "/runtime/event-contract",
}


def test_safe_stub_routes_exist(registered_paths):
    assert "/tools/execution-stub" in registered_paths
    assert "/model-router/stub-test" in registered_paths


def test_dangerous_direct_execution_routes_are_not_registered(registered_paths):
    for path in DANGEROUS_PATHS:
        assert path not in registered_paths


def test_no_disallowed_execute_suffix_routes_are_registered(registered_paths):
    disallowed = []
    for path in registered_paths:
        if path in ALLOWED_STUB_PATHS:
            continue
        if any(path.endswith(suffix) for suffix in DANGEROUS_SUFFIXES):
            disallowed.append(path)

    assert "/n8n-workflows/{id}/execute" not in registered_paths
    assert "/n8n-workflows/{workflow_id}/activate" not in registered_paths
    assert "/github-imports/{id}/execute" not in registered_paths
    assert "/model-provider-keys/{provider}/test" not in registered_paths
    assert "/model-provider-keys/{provider}/execute" not in registered_paths
    assert not disallowed, f"Disallowed execute routes found: {sorted(disallowed)}"


def test_forbidden_runtime_and_activation_routes_are_not_registered(registered_paths):
    assert "/runtime/execute" not in registered_paths
    assert "/runtime/activate" not in registered_paths
    assert "/runtime/retry" not in registered_paths
    assert "/runtime/replay" not in registered_paths
    assert "/runtime/history" not in registered_paths
    assert "/model-router/generate" not in registered_paths
    assert "/tools/execute" not in registered_paths

    for prefix in FORBIDDEN_ROUTE_PREFIXES:
        assert not any(path.startswith(prefix) for path in registered_paths), prefix

    runtime_paths = {path for path in registered_paths if path.startswith("/runtime/")}
    assert runtime_paths == ALLOWED_RUNTIME_PATHS
