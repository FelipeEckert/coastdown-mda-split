"""Compatibility-only method selection for the unrouted Standard pages."""

VALID_LEGACY_TEST_METHODS = ("traditional", "split")


def legacy_test_method_key(session_state):
    """Return a page-private key scoped to the active historical test."""
    test_id = session_state.get("active_test_id")
    suffix = test_id if isinstance(test_id, str) and test_id else "unbound"
    return f"_legacy_test_method_{suffix}"


def _valid_method(value):
    return value if value in VALID_LEGACY_TEST_METHODS else None


def legacy_test_method(session_state):
    """Resolve old method state without promoting it into active flat state."""
    private_method = _valid_method(
        session_state.get(legacy_test_method_key(session_state))
    )
    if private_method:
        return private_method

    split_flag = session_state.get("using_split_method")
    if type(split_flag) is bool:
        return "split" if split_flag else "traditional"

    flat_method = _valid_method(session_state.get("test_method"))
    if flat_method:
        return flat_method

    tests = session_state.get("tests")
    test_id = session_state.get("active_test_id")
    snapshot = (
        tests.get(test_id)
        if isinstance(tests, dict) and isinstance(test_id, str)
        else None
    )
    if isinstance(snapshot, dict):
        split_flag = snapshot.get("using_split_method")
        if type(split_flag) is bool:
            return "split" if split_flag else "traditional"

        snapshot_method = _valid_method(snapshot.get("test_method"))
        if snapshot_method:
            return snapshot_method

    return "split"


def legacy_uses_split_method(session_state):
    return legacy_test_method(session_state) == "split"
