"""Temporary browser ownership. Account IDs are hex and never use the guest prefix."""
import hashlib
import secrets
import time

from fastapi import HTTPException

COOKIE = "__Host-choreo-guest"
PREFIX = "guest:"
LIMIT_MESSAGE = "Guest upload limit reached. Sign in to add another video."


def cookie_hash(request):
    token = request.cookies.get(COOKIE)
    return hashlib.sha256(token.encode()).hexdigest() if token else None


def session(con, request):
    return con.execute("""
        SELECT hash, csrf, expires, terms_version, ? || hash AS user_id, '' AS email, '' AS email_key
        FROM guest_sessions WHERE hash=? AND expires>?
    """, (PREFIX, cookie_hash(request), time.time())).fetchone()


def start(con, cfg, request, response, terms, rate, network):
    now = time.time()
    # Keep the anonymous identity for the full weekly quota window. Each clip
    # has its own shorter expiry, independent of cookie renewal.
    ttl = max(7 * 86400, min(cfg.guest_retention_hours * 3600, cfg.retention_seconds))
    guest = session(con, request)
    if guest:
        token, csrf = request.cookies[COOKIE], guest['csrf']
        con.execute('UPDATE guest_sessions SET expires=?, terms_version=? WHERE hash=?',
                    (now + ttl, terms, guest['hash']))
    else:
        rate(con, 'guest-start:' + network, 8, 86400, now, LIMIT_MESSAGE)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        con.execute('INSERT INTO guest_sessions(hash,csrf,terms_version,expires) VALUES (?,?,?,?)',
                    (hashlib.sha256(token.encode()).hexdigest(), csrf, terms, now + ttl))
    response.set_cookie(COOKIE, token, max_age=ttl, httponly=True, secure=cfg.cookie_secure,
                        samesite='lax', path='/')
    return {'csrf': csrf}


def claim(con, cfg, request, expected_hash, user):
    """Only a successful sign-in started and finished by this guest can move its clips."""
    guest = session(con, request)
    if not guest or guest['hash'] != expected_hash:
        return False
    now = time.time()
    con.execute("""
        UPDATE upload_records SET user_id=?, email=? WHERE project IN (
            SELECT id FROM projects WHERE owner=? AND expires>?
            AND status NOT IN ('expired','deleted','removed','quarantined'))
    """, (user['id'], user['email'], guest['user_id'], now))
    con.execute("""
        UPDATE projects SET owner=?, expires=created+? WHERE owner=? AND expires>?
        AND status NOT IN ('expired','deleted','removed','quarantined')
    """, (user['id'], cfg.retention_seconds, guest['user_id'], now))
    con.execute('DELETE FROM guest_sessions WHERE hash=?', (guest['hash'],))
    return True


def check_quota(con, cfg, owner, network, now):
    for window, limit in ((86400, cfg.guest_uploads_day), (7 * 86400, cfg.guest_uploads_week)):
        for column, value in (('guest_owner', owner), ('ip_hash', network)):
            count = con.execute(f"""
                SELECT count(*) FROM upload_records WHERE guest_owner IS NOT NULL
                AND {column}=? AND created>?
            """, (value, now - window)).fetchone()[0]
            if count >= limit:
                raise HTTPException(401, LIMIT_MESSAGE)
