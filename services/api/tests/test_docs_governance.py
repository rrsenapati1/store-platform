from pathlib import Path


def test_docs_spine_exists_for_canonical_governance():
    root = Path(__file__).resolve().parents[3]
    required_paths = [
        "docs/DOCS_INDEX.md",
        "docs/PROJECT_CONTEXT.md",
        "docs/STORE_CANONICAL_BLUEPRINT.md",
        "docs/API_CONTRACT_MATRIX.md",
        "docs/TASK_LEDGER.md",
        "docs/WORKLOG.md",
        "docs/HANDOFF_TEMPLATE.md",
        "docs/context/MODULE_MAP.md",
        "docs/runbooks/dev-workflow.md",
    ]

    missing = [path for path in required_paths if not (root / path).exists()]

    assert missing == []
