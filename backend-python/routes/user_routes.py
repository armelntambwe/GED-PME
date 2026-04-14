# routes/user_routes.py
from flask import request, jsonify
from middleware.auth import token_required, role_required
from models.user import User
from models.log import Log
from models.notification import Notification
from werkzeug.security import generate_password_hash
from utils.db import get_db

def register_user_routes(app):

    @app.route("/users", methods=["GET"])
    @token_required
    def get_users():
        if request.user_role not in ['admin_global', 'admin_pme']:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        entreprise_id = getattr(request, 'user_entreprise_id', None)

        if request.user_role == 'admin_pme':
            users = User.get_employees(entreprise_id)
        else:
            users = User.get_all()

        return jsonify({
            "success": True,
            "count": len(users),
            "users": users
        }), 200

    @app.route("/users/<int:user_id>/desactiver", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def desactiver_user(user_id):
        User.deactivate(user_id)
        Log.create('DESACTIVATION_USER', f"Utilisateur {user_id} désactivé", request.user_id)
        
        Notification.create(
            user_id=request.user_id,
            type_notif='USER_DESACTIVE',
            message=f"L'utilisateur a été désactivé",
            lien='/dashboard-pme?tab=employes'
        )
        
        return jsonify({"success": True, "message": "Utilisateur désactivé"}), 200

    @app.route("/admin/employes", methods=["POST"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def create_employe():
        data = request.json

        if not data or "nom" not in data or "email" not in data:
            return jsonify({"success": False, "message": "Nom et email requis"}), 400

        nom = data["nom"]
        email = data["email"]
        telephone = data.get("telephone", "")
        password = data.get("password", "employe123")
        password_hash = generate_password_hash(password)
        entreprise_id = getattr(request, 'user_entreprise_id', 1)

        existing_user = User.find_by_email(email)
        if existing_user:
            return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

        user_id = User.create(nom, email, password_hash, 'employe', telephone, entreprise_id)

        Log.create('CREATION_EMPLOYE', f"Employé '{nom}' créé", request.user_id)
        
        Notification.create(
            user_id=request.user_id,
            type_notif='EMPLOYE_CREE',
            message=f"L'employé {nom} a été créé",
            lien='/dashboard-pme?tab=employes'
        )

        return jsonify({
            "success": True,
            "message": "Employé créé",
            "user_id": user_id
        }), 201