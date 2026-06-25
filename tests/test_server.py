import pytest


def test_server_imports_when_dependencies_are_installed():
    pytest.importorskip("fastapi")
    pytest.importorskip("multipart")

    import shiksha_cast.server as server

    assert server.app.title == "Shiksha-Cast API"
