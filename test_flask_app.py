import os
#import tempfile

import pytest

@pytest.fixture
def client():
    #db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    #s = tempfile.mkstemp()
    os.environ['DATABASE_URL' ] = 'sqlite:///../test_ct_db.db'
    #db_fd, app.config['SQLALCHEMY_DATABASE_URI'] = tempfile.mkstemp()

    from app import app, db

    app.config['TESTING'] = True
    client = app.test_client()

    #with app.app_context():
    #    init_db()
    db.create_all()

    yield client

    #os.close(db_fd)
    #os.unlink(app.config['DATABASE'])
    #os.unlink(app.config['SQLALCHEMY_DATABASE_URI'])

def test_home_page(client):
    """Tests for home page."""

    rv = client.get('/')
    assert b'Workflow' in rv.data

 def test_help_page(client):
    """Tests for help page."""

    rv = client.get('/')
    assert b'First.ipynb' in rv.data
