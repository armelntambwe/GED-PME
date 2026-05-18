#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import app

print("Testing login endpoint...")
client = app.test_client()

# Try admin login
resp = client.post('/api/user/login', json={
    'email': 'admin@gmail.com',
    'password': 'admin123'
})

print("Status:", resp.status_code)
print("Response:", resp.get_json() if resp.status_code in [200, 201] else resp.data[:200])

if resp.status_code == 200:
    data = resp.get_json()
    token = data.get('token')
    print("\nToken obtained:", token[:30] + "..." if token else "NO TOKEN")
    
    # Test a protected endpoint
    print("\nTesting /api/pme/stats with token...")
    resp2 = client.get('/api/pme/stats', headers={'Authorization': 'Bearer ' + token})
    print("Status:", resp2.status_code)
    print("Response:", resp2.data[:300])
