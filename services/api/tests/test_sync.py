from store_api.sync import build_pull_response, resolve_mutation_conflict


def test_sync_rejects_stale_versions():
    result = resolve_mutation_conflict(client_version=1, server_version=2)

    assert result.accepted is False
    assert result.conflict is True
    assert result.next_version == 2


def test_pull_response_uses_latest_version_as_cursor():
    response = build_pull_response(
        [
            {"id": "row-1", "version": 2},
            {"id": "row-2", "version": 5},
        ]
    )

    assert response["cursor"] == 5
