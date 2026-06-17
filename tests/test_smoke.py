"""스모크 테스트 — 앱이 import되고 핵심 라우트가 응답하는지만 확인.
탭(기능)이 늘어도 깨지지 않도록 최소·안정 범위만 검증한다."""
import importlib


def _client():
    mod = importlib.import_module("app")
    mod.app.config["TESTING"] = True
    mod.init_db()  # 기본 DB(board.db)에 테이블 생성 — CI 워크스페이스에서만 생성됨
    return mod.app.test_client()


def test_app_imports():
    import app  # noqa: F401


def test_index_ok():
    resp = _client().get("/")
    assert resp.status_code == 200
