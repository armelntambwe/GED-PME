# routes/authentification_routes.py
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db
from utils.jwt_manager import generer_token

def register_authentification_routes(app):

    @app.route("/api/user/register", methods=["POST"])
    def user_register():
        data = request.json
        if not data or "nom" not in data or "email" not in data or "password" not in data:
            return jsonify({"message": "Données manquantes"}), 400

        nom = data["nom"]
        email = data["email"]
        password = data["password"]
        role = data.get("role", "employe")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

        password_hash = generate_password_hash(password)
        cur.execute("""
            INSERT INTO users (nom, email, password, role, actif)
            VALUES (%s, %s, %s, %s, 1)
        """, (nom, email, password_hash, role))
        user_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Utilisateur créé", "user_id": user_id}), 201

    @app.route("/api/user/login", methods=["POST"])
    def user_login():
        data = request.json
        if not data or "email" not in data or "password" not in data:
            return jsonify({"success": False, "message": "Données manquantes"}), 400

        email = data["email"]
        password = data["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, email, password, role, entreprise_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

        if not check_password_hash(user['password'], password):
            return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401

        token = generer_token(user['id'], user['role'], user.get('entreprise_id'))

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user['id'],
                "nom": user['nom'],
                "email": user['email'],
                "role": user['role'],
                "entreprise_id": user.get('entreprise_id')
            }
        }), 200