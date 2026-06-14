#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test database connection and data retrieval"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import app
from extensions import db
from models_sqlalchemy.user import User
from models_sqlalchemy.entreprise import Entreprise

print("[Test] Database Connection and Data Retrieval\n")

with app.app_context():
    try:
        # Test 1: Database connection
        print("[1] Testing database connection...")
        result = db.session.execute(db.text("SELECT 1"))
        print("[OK] Database connection works\n")
        
        # Test 2: Count users
        print("[2] Counting users...")
        user_count = User.query.count()
        print("[OK] Total users: {}\n".format(user_count))
        
        # Test 3: Count enterprises
        print("[3] Counting enterprises...")
        ent_count = Entreprise.query.count()
        print("[OK] Total enterprises: {}\n".format(ent_count))
        
        # Test 4: List first 3 users
        print("[4] First 3 users:")
        users = User.query.limit(3).all()
        for u in users:
            print("  - ID: {}, Name: {}, Email: {}, Role: {}".format(u.id, u.nom, u.email, u.role))
        
        if not users:
            print("  [WARNING] No users found")
        
        print("\n[5] First 3 enterprises:")
        enterprises = Entreprise.query.limit(3).all()
        for e in enterprises:
            print("  - ID: {}, Name: {}, Email: {}".format(e.id, e.nom, e.email))
        
        if not enterprises:
            print("  [WARNING] No enterprises found")
        
        print("\n[SUCCESS] All tests passed!")
        
    except Exception as e:
        print("[ERROR] {}".format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)
