#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Manual test of export endpoint"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import app
from utils.jwt_manager import generer_token
from models_sqlalchemy.user import User

# Get a valid token
with app.app_context():
    admin = User.query.filter_by(role='admin_global').first()
    if admin:
        token = generer_token(admin.id, admin.role, admin.entreprise_id)
        print("[OK] Token generated for user: {}".format(admin.nom))
    else:
        print("[ERROR] No admin_global user found")
        sys.exit(1)

# Test the export endpoint using test client
client = app.test_client()
headers = {'Authorization': 'Bearer {}'.format(token)}

print("\n[Test] GET /api/admin-global/entreprises/export")
response = client.get('/api/admin-global/entreprises/export', headers=headers)
print("Status: {}".format(response.status_code))
print("Content-Type: {}".format(response.headers.get('Content-Type')))
print("Data type: {}".format(type(response.data)))
print("Data length: {}".format(len(response.data)))

if response.status_code == 200:
    print("First 200 bytes: {}".format(response.data[:200]))
else:
    print("Error response: {}".format(response.data.decode('utf-8')))
