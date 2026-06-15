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
    assert not disallowed, f"Disallowed execute routes found: {sorted(disallowed)}"
