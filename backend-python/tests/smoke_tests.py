import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app
from flask import url_for


def make_sample_arg(arg_name):
    # return a simple sample for most common ids
    return '1'


def is_interesting(rule_str):
    kws = ['notif', 'notification', 'log', 'export', 'document', 'pme', 'entreprise', 'user', 'utilisateur']
    s = rule_str.lower()
    return any(k in s for k in kws)


def build_url(rule):
    # try to build with url_for inside test_request_context
    with app.test_request_context():
        try:
            kwargs = {arg: make_sample_arg(arg) for arg in rule.arguments}
            return url_for(rule.endpoint, **kwargs)
        except Exception:
            # fallback: simple string replace
            u = rule.rule
            for arg in rule.arguments:
                u = u.replace(f'<{arg}>', '1').replace(f'<int:{arg}>', '1').replace(f'<string:{arg}>', '1')
            return u


def run():
    client = app.test_client()
    
    # Step 1: Try to login
    print('Attempting login to get JWT token...')
    login_resp = client.post('/api/user/login', json={
        'email': 'admin@test.com',
        'password': 'test123'
    })
    token = None
    if login_resp.status_code == 200:
        try:
            data = login_resp.get_json()
            token = data.get('token')
            print('[OK] Login successful, token: {}...'.format(token[:20] if token else 'None'))
        except Exception as e:
            print('[FAIL] Login response parsing error: {}'.format(e))
    else:
        print('[FAIL] Login failed with status {}'.format(login_resp.status_code))
    
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    print('\nFound {} routes. Filtering interesting ones...'.format(len(rules)))
    interesting = [r for r in rules if 'GET' in r.methods and is_interesting(r.rule)]
    print('Will test {} routes:\n'.format(len(interesting)))

    headers = {}
    if token:
        headers['Authorization'] = 'Bearer {}'.format(token)

    for r in interesting:
        url = build_url(r)
        print('---')
        print('Rule: {} -> endpoint: {} | URL used: {}'.format(r.rule, r.endpoint, url))
        try:
            resp = client.get(url, headers=headers)
            ct = resp.headers.get('Content-Type', '')
            length = len(resp.data or b'')
            print('Status: {} | Content-Type: {} | Bytes: {}'.format(resp.status_code, ct, length))
            snippet = resp.data[:400]
            try:
                decoded = snippet.decode('utf-8', errors='replace')
                print('Body (start): {}'.format(decoded))
            except Exception:
                print('Body (bytes): {}'.format(snippet))
        except Exception as e:
            print('Request failed: {}'.format(repr(e)))


if __name__ == '__main__':
    print('Smoke test started at', datetime.utcnow().isoformat())
    try:
        run()
    except Exception as e:
        print('Smoke script error:', e)
        sys.exit(2)
    print('Smoke test finished at', datetime.utcnow().isoformat())
