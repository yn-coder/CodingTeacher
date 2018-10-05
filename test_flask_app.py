import os

import pytest
import json

from app import db, Question

@pytest.fixture
def client():
    os.environ['DATABASE_URL' ] = 'sqlite:////test_sqlite.db'

    from app import app

    app.config['TESTING'] = True
    client = app.test_client()

    db.create_all()

    yield client

def test_home_page(client):
    """Tests for home page."""

    rv = client.get('/')
    assert b'Workflow' in rv.data

def test_help_page(client):
    """Tests for help page."""

    rv = client.get('/help/')
    assert b'First.ipynb' in rv.data

def test_help_page_first_ipynb(client):
    """Tests for help page 'First.ipynb'."""

    rv = client.get('/help/resource/first.ipynb')
    assert b'First.ipynb book' in rv.data

def test_help_page_special(client):
    """Tests for help page in subfolder."""

    rv = client.get('/help/resource/more/special')
    assert b'Special page in subfolder' in rv.data

def test_help_pagezero(client):
    """Tests for help page if page name is empty."""

    rv = client.get('/help/resource/')
    assert rv.status == '404 NOT FOUND'

def test_help_no_page(client):
    """Tests for help page if no page is exist."""

    rv = client.get('/help/resource/no_such_page/')
    assert b'No special resource is exists!' in rv.data

def test_help_page_with_double_dots(client):
    """Tests for help page if page name is empty."""

    rv = client.get('/help/resource/../index/')
    assert b'No special resource is exists!' in rv.data

def test_get_empty_user_list(client):
    from app import User
    assert User.query.count() == 0

def test_try_save_question2db(client):
    nq = Question(file_name = 'test_file_name', file_url = '2', description = '3', cell_code = '4', cell_output = '5' )
    db.session.add(nq)
    db.session.commit()
    assert nq.id > 0

def test_calc_answer_empty():
    from app import calc_answer
    assert calc_answer( '', '', 0, '' ) == 'Can''t parse the question!'

def test_calc_answer_python_cant_parse(client):
    d = dict( file_name = 'file name', file_url = '-', description = '-', cell_code = '-', cell_output = '-' )
    rv = client.post('/help/post_new_q/', data = d )
    res_msg = json.loads(rv.data)
    assert 'parse' in res_msg['msg']

def test_calc_answer_python_NameError(client):
    d = data=dict( file_name = 'file name', file_url = 'test_url', description = '-', cell_code = '', cell_output = '[{"ename":"NameError", "evalue":"name ''j'' is not defined","output_type":"error","traceback": "" }]' )
    rv = client.post('/help/post_new_q/', data = d )
    res_msg = json.loads(rv.data)
    assert 'Read about NameError' in res_msg['msg']
