import pytest
from helpdesk import create_app
from helpdesk.db import init_db

@pytest.fixture
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "helpdesk-test.sqlite3"),
    })
    with application.app_context():
        init_db()
    return application

@pytest.fixture
def client(app):
    return app.test_client()
