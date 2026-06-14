#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test POST and PUT endpoints"""
import sys
import json
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

client = app.test_client()
headers = {
    'Authorization': 'Bearer {}'.format(token),
    'Content-Type': 'application/json'
}

# Test 1: POST /api/admin-global/entreprises
print("\n[Test 1] POST /api/admin-global/entreprises")
response = client.post('/api/admin-global/entreprises', 
    headers=headers,
    data=json.dumps({
        'nom': 'Test Company API',
        'email': 'test@api.com',
        'telephone': '123456',
        'adresse': 'Test Address'
    })
)
print("Status: {}".format(response.status_code))
print("Response: {}".format(response.data.decode('utf-8')[:300]))

if response.status_code == 201:
    data = response.get_json()
    new_id = data.get('id')
    print("Created ID: {}".format(new_id))
    
    # Test 2: PUT /api/admin-global/entreprises/<id>
    print("\n[Test 2] PUT /api/admin-global/entreprises/{}".format(new_id))
    response2 = client.put('/api/admin-global/entreprises/{}'.format(new_id),
        headers=headers,
        data=json.dumps({
            'nom': 'Updated Test Company'
        })
    )
    print("Status: {}".format(response2.status_code))
    print("Response: {}".format(response2.data.decode('utf-8')))
