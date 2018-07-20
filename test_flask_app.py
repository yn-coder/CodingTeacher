import os
import tempfile

import pytest

from app import app


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    #with app.app_context():
    #    init_db()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])
    
def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert b'Workflow' in rv.data    