# routes/user_routes.py
from flask import request, jsonify
from middleware.auth import token_required, role_required
from services.user_service import UserService
from models_sqlalchemy import User, Entreprise, Log, Notification
from extensions import db
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def register_user_routes(app):

    @app.route("/users", methods=["GET"])
    @token_required
    def get_users():
        try:
            users = User.query.order_by(User.id.desc()).all()
            return jsonify({"success": True, "users": [u.to_dict() for u in users]}), 200
        except Exception as e:
            logger.error(f"Erreur get_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/users/<int:user_id>/desactiver", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def desactiver_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            user.actif = False
            db.session.add(user)

            log = Log(
                action='DESACTIVATION_USER',
                description=f"Utilisateur {user_id} désactivé",
                user_id=request.user_id,
                date_action=datetime.utcnow()
            )
            db.session.add(log)

            notification = Notification(
                user_id=request.user_id,
                type_notif='USER_DESACTIVE',
                message="L'utilisateur a été désactivé",
                lien='/dashboard-pme?tab=employes',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Utilisateur désactivé"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur desactiver_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/admin/employes", methods=["GET"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def get_employes():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            query = User.query.filter_by(role='employe')
            if entreprise_id is not None:
                query = query.filter_by(entreprise_id=entreprise_id)
            employes = query.order_by(User.id.desc()).all()
            return jsonify({"success": True, "employes": [u.to_dict() for u in employes]}), 200
        except Exception as e:
            logger.error(f"Erreur get_employes: {e}")
            return jsonify({"success": True, "employes": []}), 200

    @app.route("/admin/employes", methods=["POST"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def create_employe():
        try:
            data = request.json or {}
            nom = data.get('nom', '').strip()
            email = data.get('email', '').strip()
            telephone = data.get('telephone', '').strip()
            password = data.get('password', 'employe123')

            if not nom or not email:
                return jsonify({"success": False, "message": "Nom et email requis"}), 400
            if len(password) < 6:
                return jsonify({"success": False, "message": "Le mot de passe doit avoir au moins 6 caractères"}), 400

            existing_user = UserService.get_user_by_email(email)
            if existing_user:
                return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

            entreprise_id = getattr(request, 'user_entreprise_id', None)
            password_hash = generate_password_hash(password)
            user_id = UserService.create_user(
                nom=nom,
                email=email,
                password_hash=password_hash,
                role='employe',
                telephone=telephone,
                entreprise_id=entreprise_id
            )

            log = Log(
                action='CREATION_EMPLOYE',
                description=f"Employé '{nom}' créé",
                user_id=request.user_id,
                date_action=datetime.utcnow()
            )
            db.session.add(log)

            notification = Notification(
                user_id=request.user_id,
                type_notif='EMPLOYE_CREE',
                message=f"L'employé {nom} a été créé",
                lien='/dashboard-pme?tab=employes',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Employé créé", "user_id": user_id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_employe: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/info", methods=["GET"])
    @token_required
    def get_api_entreprise_info():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            return jsonify({
                "success": True,
                "id": entreprise.id,
                "nom": entreprise.nom,
                "adresse": entreprise.adresse or '',
                "telephone": entreprise.telephone or '',
                "email": entreprise.email or ''
            }), 200
        except Exception as e:
            logger.error(f"Erreur get_api_entreprise_info: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/info", methods=["PUT"])
    @token_required
    def update_api_entreprise_info():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            data = request.json or {}
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

            entreprise.nom = data.get('nom', entreprise.nom)
            entreprise.adresse = data.get('adresse', entreprise.adresse)
            entreprise.telephone = data.get('telephone', entreprise.telephone)
            entreprise.email = data.get('email', entreprise.email)
            db.session.commit()

            return jsonify({"success": True, "message": "Entreprise mise à jour"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_api_entreprise_info: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/profile", methods=["GET"])
    @token_required
    def get_api_user_profile():
        try:
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            return jsonify({"success": True, **user.to_dict()}), 200
        except Exception as e:
            logger.error(f"Erreur get_api_user_profile: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/profile", methods=["PUT"])
    @token_required
    def update_api_user_profile():
        try:
            data = request.json or {}
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            if 'nom' in data:
                user.nom = data.get('nom', user.nom)
            if 'telephone' in data:
                user.telephone = data.get('telephone', user.telephone)
            if 'password' in data and data.get('password'):
                if len(data.get('password')) < 6:
                    return jsonify({"success": False, "message": "Le mot de passe doit avoir au moins 6 caractères"}), 400
                user.password = generate_password_hash(data.get('password'))

            db.session.commit()
            return jsonify({"success": True, "message": "Profil mis à jour"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_api_user_profile: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/logs", methods=["GET"])
    @token_required
    @role_required(['admin_pme'])
    def get_api_entreprise_logs():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            if entreprise_id is None:
                return jsonify({"success": False, "message": "Entreprise non identifiée"}), 400

            logs = Log.query.join(User, Log.user_id == User.id).filter(User.entreprise_id == entreprise_id).order_by(Log.date_action.desc()).limit(50).all()
            return jsonify({"success": True, "logs": [log.to_dict() for log in logs]}), 200
        except Exception as e:
            logger.error(f"Erreur get_api_entreprise_logs: {e}")
            return jsonify({"success": True, "logs": []}), 200
