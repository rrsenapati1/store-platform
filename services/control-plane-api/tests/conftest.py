from pathlib import Path
import sys
from uuid import uuid4


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def sqlite_test_database_url(name: str) -> str:
    tmp_root = API_ROOT / ".tmp-tests"
    tmp_root.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{(tmp_root / f'{name}-{uuid4().hex}.db').as_posix()}"
