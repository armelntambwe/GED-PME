#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test export CSV"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import app
from extensions import db
from services.admin_service_orm import AdminService
from io import BytesIO, StringIO
import csv
from datetime import datetime

print("[Test] CSV Export\n")

with app.app_context():
    try:
        # Get companies
        companies = AdminService.list_all_companies(limit=5)
        print("[OK] Got {} companies".format(len(companies)))
        
        # Try to create CSV
        output_text = StringIO()
        writer = csv.writer(output_text, quoting=csv.QUOTE_ALL)
        writer.writerow(['ID', 'Nom', 'Email'])
        
        for c in companies:
            print("  Company: {}".format(c))
            writer.writerow([
                str(c.get('id', '')), 
                str(c.get('nom', '')), 
                str(c.get('email', ''))
            ])
        
        print("[OK] CSV written to StringIO")
        
        # Convert to bytes
        csv_text = output_text.getvalue()
        print("[OK] StringIO content type: {}".format(type(csv_text)))
        print("[OK] First 100 chars: {}".format(csv_text[:100]))
        
        # Encode to bytes
        csv_bytes = csv_text.encode('utf-8-sig')
        print("[OK] Encoded to bytes, size: {}".format(len(csv_bytes)))
        
        # Create BytesIO
        bytes_out = BytesIO(csv_bytes)
        bytes_out.seek(0)
        print("[OK] BytesIO created, seekable: {}".format(bytes_out.seekable()))
        
        print("\n[SUCCESS] Export test passed!")
        
    except Exception as e:
        print("[ERROR] {}".format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)
