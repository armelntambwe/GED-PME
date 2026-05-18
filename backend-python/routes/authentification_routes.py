# routes/authentification_routes.py
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.jwt_manager import generer_token
from services.user_service import UserService


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

        existing_user = UserService.get_user_by_email(email)
        if existing_user:
            return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

        password_hash = generate_password_hash(password)
        user_id = UserService.create_user(nom, email, password_hash, role)

        return jsonify({"success": True, "message": "Utilisateur créé", "user_id": user_id}), 201

    @app.route("/api/user/login", methods=["POST"])
    def user_login():
        data = request.json
        if not data or "email" not in data or "password" not in data:
            return jsonify({"success": False, "message": "Données manquantes"}), 400

        email = data["email"]
        password = data["password"]

        user = UserService.get_user_by_email_raw(email)
        if not user:
            return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

        if not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401

        token = generer_token(user.id, user.role, user.entreprise_id)

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "nom": user.nom,
                "email": user.email,
                "role": user.role,
                "entreprise_id": user.entreprise_id
            }
        }), 200