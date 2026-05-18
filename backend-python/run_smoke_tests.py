#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smoke test script with proper authentication
"""
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app
from extensions import db
from models_sqlalchemy.user import User
from models_sqlalchemy.entreprise import Entreprise
from werkzeug.security import generate_password_hash

def setup_test_user():
    """Create or verify test user exists"""
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(email='test@test.com').first()
        if not test_user:
            # Create test company
            test_company = Entreprise.query.filter_by(nom='Test Company').first()
            if not test_company:
                test_company = Entreprise(
                    nom='Test Company',
                    email='company@test.com',
                    adresse='Test Address',
                    statut='actif'
                )
                db.session.add(test_company)
                db.session.flush()
            
            # Create test admin_pme user
            test_user = User(
                nom='Test Admin',
                email='test@test.com',
                password=generate_password_hash('test123'),
                role='admin_pme',
                entreprise_id=test_company.id,
                actif=True
            )
            db.session.add(test_user)
            db.session.commit()
            print('[OK] Test user created')
        else:
            print('[OK] Test user exists')
        
        return test_user

def run_smoke_tests():
    """Run smoke tests with authentication"""
    with app.app_context():
        setup_test_user()
    
    client = app.test_client()
    
    print('Smoke test started at {}'.format(datetime.utcnow().isoformat()))
    
    # Step 1: Login
    print('\n[Step 1] Attempting login...')
    login_resp = client.post('/api/user/login', json={
        'email': 'test@test.com',
        'password': 'test123'
    })
    
    print('Login response status: {}'.format(login_resp.status_code))
    
    token = None
    if login_resp.status_code == 200:
        data = login_resp.get_json()
        token = data.get('token')
        print('[OK] Login successful, token obtained')
    else:
        print('[FAIL] Login failed')
        print('Response: {}'.format(login_resp.data[:300]))
        return
    
    headers = {'Authorization': 'Bearer {}'.format(token)}
    
    # Test key endpoints
    test_endpoints = [
        ('/api/pme/stats', 'GET', 'PME stats'),
        ('/api/pme/documents', 'GET', 'PME documents'),
        ('/api/pme/employes', 'GET', 'PME employees'),
        ('/api/pme/validation', 'GET', 'PME validation'),
        ('/api/pme/corbeille', 'GET', 'PME trash'),
        ('/notifications/all', 'GET', 'All notifications'),
        ('/notifications/count', 'GET', 'Notifications count'),
        ('/api/entreprise/info', 'GET', 'Company info'),
        ('/api/entreprise/logs', 'GET', 'Company logs'),
    ]
    
    print('\n[Step 2] Testing {} endpoints...'.format(len(test_endpoints)))
    
    results = {'success': 0, 'fail': 0}
    
    for url, method, desc in test_endpoints:
        print('\nTesting: {} {} ({})'.format(method, url, desc))
        
        try:
            if method == 'GET':
                resp = client.get(url, headers=headers)
            else:
                resp = client.post(url, headers=headers, json={})
            
            status = resp.status_code
            ct = resp.headers.get('Content-Type', '')
            
            print('  Status: {} | Content-Type: {}'.format(status, ct))
            
            if status in [200, 201]:
                results['success'] += 1
                try:
                    data = resp.get_json()
                    if data:
                        keys = list(data.keys())[:5]
                        print('  [OK] Response keys: {}'.format(keys))
                except:
                    print('  [OK] Response OK (non-JSON)')
            else:
                results['fail'] += 1
                print('  [FAIL] Status {}'.format(status))
                try:
                    print('  Response: {}'.format(resp.get_json()))
                except:
                    print('  Response: {}'.format(resp.data[:100]))
        
        except Exception as e:
            results['fail'] += 1
            print('  [ERROR] {}'.format(str(e)))
    
    print('\n=== Test Summary ===')
    print('Passed: {}'.format(results['success']))
    print('Failed: {}'.format(results['fail']))
    print('Smoke test finished at {}'.format(datetime.utcnow().isoformat()))


if __name__ == '__main__':
    try:
        run_smoke_tests()
    except Exception as e:
        print('[CRITICAL ERROR] {}'.format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(2)
