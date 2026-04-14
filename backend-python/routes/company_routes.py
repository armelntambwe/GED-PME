# routes/company_routes.py
from flask import request, jsonify
from werkzeug.security import generate_password_hash
from utils.db import get_db

def register_company_routes(app):

    @app.route("/api/register-company", methods=["POST"])
    def company_register():
        data = request.json

        if not data or not data.get('entreprise_nom') or not data.get('email') or not data.get('password'):
            return jsonify({"success": False, "message": "Données manquantes"}), 400

        entreprise_nom = data['entreprise_nom']
        responsable_nom = data['responsable_nom']
        email = data['email']
        telephone = data.get('telephone', '')
        password = data['password']

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Cet email est déjà utilisé"}), 409

        try:
            cur.execute("""
                INSERT INTO entreprises (nom, telephone, email, statut)
                VALUES (%s, %s, %s, 'actif')
            """, (entreprise_nom, telephone, email))
            entreprise_id = cur.lastrowid

            password_hash = generate_password_hash(password)
            cur.execute("""
                INSERT INTO users (nom, email, password, telephone, role, actif, entreprise_id)
                VALUES (%s, %s, %s, %s, 'admin_pme', 1, %s)
            """, (responsable_nom, email, password_hash, telephone, entreprise_id))

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"success": True, "message": "Entreprise créée avec succès"}), 201

        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": str(e)}), 500