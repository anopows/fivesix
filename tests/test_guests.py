import concurrent.futures
import re
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from choreo import guests
from choreo.retention import extend_available
from choreo.worker import Worker
from test_service import begin, open_uploads, ready, room, start_guest, unlock


def browser(app, cfg):
    return TestClient(app, base_url=cfg.origin, headers={'Origin': cfg.origin})


@pytest.mark.parametrize('email', ['new@example.com', 'admin@example.com'])
def test_private_upload_return_and_claim(room, email):
    c, app, cfg, store = room
    open_uploads(app)
    cookie = start_guest(c).headers['set-cookie'].lower()
    assert all(attr in cookie for attr in ('secure', 'httponly', 'samesite=lax', 'path=/'))
    pid = ready(c, app)
    path = f'/api/projects/{pid}'
    old_cookie = c.cookies.get(guests.COOKIE)
    returning = browser(app, cfg)
    returning.cookies.update(c.cookies)
    assert returning.get('/api/bootstrap').json()['guest']
    assert returning.get('/api/projects').json()['projects'][0]['id'] == pid
    practice = c.get(path + '/practice').json()
    assert practice['owner'] and not practice['shared']
    assert 47 < (practice['expires'] - time.time()) / 3600 <= 48
    assert c.post(path + '/share', json={}).status_code == 401

    visitor = browser(app, cfg)
    start_guest(visitor)
    assert visitor.get('/api/projects').json()['projects'] == []
    for url in (path, path + '/practice', practice['videoUrl'], practice['posterUrl']):
        assert visitor.get(url).status_code == 404
    assert visitor.post(path + '/exports', json={'revision': 0, 'speed': 1}).status_code == 404
    job = c.post(path + '/exports', json={'revision': 0, 'speed': 1}).json()
    assert visitor.get(path + '/exports/' + job['id']).status_code == 404
    unlock(c, email)
    assert c.get('/api/projects').json()['projects'][0]['id'] == pid
    assert c.cookies.get(guests.COOKIE) is None
    assert 89 < (c.get(path).json()['expires'] - time.time()) / 86400 <= 90
    assert returning.cookies.get(guests.COOKIE) == old_cookie
    assert returning.get('/api/projects').status_code == 401
    assert visitor.get(path + '/practice').status_code == 404
    assert c.post(path + '/share', json={}).status_code == 200
    assert visitor.get(path + '/practice').json()['owner'] is False
    assert begin(c).status_code == 200
    assert begin(visitor).status_code == 401


def test_guest_limits_are_atomic_and_survive_cookie_changes_and_deletion(room):
    c, app, cfg, _ = room
    open_uploads(app)
    start_guest(c)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: begin(c), range(2)))
    assert sorted(r.status_code for r in results) == [200, 401]
    pid = next(r.json()['id'] for r in results if r.is_success)
    assert begin(c, request_id=pid).json()['id'] == pid
    assert c.delete('/api/projects/' + pid).status_code == 200
    other = browser(app, cfg)
    start_guest(other)
    assert 'Sign in' in begin(other).json()['detail']
    with app.state.db.connect(write=True) as con:
        con.execute('UPDATE upload_records SET created=created-90000')
    pid = begin(other).json()['id']
    other.delete('/api/projects/' + pid)
    with app.state.db.connect(write=True) as con:
        con.execute('UPDATE upload_records SET created=created-90000')
    assert begin(c).status_code == 401


def test_expiration_blocks_reads_claims_and_removes_media(room):
    c, app, cfg, store = room
    open_uploads(app)
    start_guest(c)
    pid = ready(c, app)
    now = time.time()
    assert extend_available(app.state.db, cfg.retention_seconds, apply=True) == 0
    with app.state.db.connect(write=True) as con:
        con.execute('UPDATE projects SET expires=? WHERE id=?', (now-1,pid))
    assert c.get('/api/projects').json()['projects'] == []
    assert c.get(f'/api/projects/{pid}/practice').status_code == 404
    unlock(c)
    assert c.get('/api/projects').json()['projects'] == []
    Worker(cfg, store).cleanup()
    with app.state.db.connect() as con:
        p = con.execute('SELECT status,cleanup_done,owner FROM projects WHERE id=?', (pid,)).fetchone()
        assert p['status'] == 'expired' and p['cleanup_done'] and p['owner'].startswith(guests.PREFIX)
    assert store.inventory(pid) == []


def test_guest_email_link_must_finish_in_requesting_browser(room):
    c, app, cfg, _ = room
    start_guest(c)
    assert c.post('/api/auth/email', json={'email':'admin@example.com','terms':1,'token':uuid.uuid4().hex}).is_success
    token = re.search(r'#t=([\w-]+)',c.messages[-1].get_body(preferencelist=('plain',)).get_content())[1]
    other = browser(app, cfg)
    assert other.post('/api/auth/email/confirm', json={'token':token}).status_code == 409
    assert c.post('/api/auth/email/confirm', json={'token':token}).is_success


def test_guest_uses_existing_pause_terms_and_csrf_guards(room):
    c, app, cfg, _ = room
    assert c.post('/api/guest-session', json={'terms':0}).status_code == 409
    start_guest(c)
    assert begin(c).status_code == 503
    open_uploads(app)
    c.headers['X-CSRF-Token'] = 'invalid'
    assert begin(c).status_code == 403
    c.headers['Origin'] = 'https://other.test'
    assert c.post('/api/guest-session', json={'terms':1}).status_code == 403
