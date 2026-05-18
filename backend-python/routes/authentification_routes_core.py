# routes/authentification_routes_core.py
"""
Routes d'authentification utilisant DatabaseService (version SQLAlchemy Core)
Remplace authentification_routes.py progressivement
"""

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from services.database_service import DatabaseService
from utils.jwt_manager import generer_token
import logging

logger = logging.getLogger(__name__)


def register_authentification_routes_core(app):
    """Enregistre les routes d'authentification avec DatabaseService."""

    @app.route("/api/auth/register", methods=["POST"])
    def user_register_core():
        """Endpoint d'inscription - VERSION SERVICE"""
        try:
            data = request.json
            
            # Validation
            if not data or not all(k in data for k in ["nom", "email", "password"]):
                return jsonify({
                    "success": False, 
                    "message": "Données manquantes: nom, email, password requis"
                }), 400

            nom = data["nom"].strip()
            email = data["email"].strip().lower()
            password = data["password"]
            role = data.get("role", "employe")
            telephone = data.get("telephone", "")
            entreprise_id = data.get("entreprise_id", 1)

            # Vérifier si l'email existe déjà
            existing = DatabaseService.get_user_by_email(email)
            if existing:
                return jsonify({
                    "success": False, 
                    "message": "Email déjà utilisé"
                }), 409

            # Hash et création
            password_hash = generate_password_hash(password)
            user_id = DatabaseService.create_user(
                nom=nom,
                email=email,
                password_hash=password_hash,
                role=role,
                telephone=telephone,
                entreprise_id=entreprise_id
            )

            logger.info(f"Nouvel utilisateur créé: {email} (ID: {user_id})")

            return jsonify({
                "success": True,
                "message": "Utilisateur créé avec succès",
                "user_id": user_id
            }), 201

        except Exception as e:
            logger.error(f"Erreur inscription: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500

    @app.route("/api/auth/login", methods=["POST"])
    def user_login_core():
        """Endpoint de connexion - VERSION SERVICE"""
        try:
            data = request.json
            
            if not data or "email" not in data or "password" not in data:
                return jsonify({
                    "success": False,
                    "message": "Email et mot de passe requis"
                }), 400

            email = data["email"].strip().lower()
            password = data["password"]

            # Récupérer l'utilisateur
            user = DatabaseService.get_user_by_email(email)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404

            # Vérifier le mot de passe
            if not check_password_hash(user['password'], password):
                return jsonify({
                    "success": False,
                    "message": "Mot de passe incorrect"
                }), 401

            # Vérifier que le compte est actif
            if not user['actif']:
                return jsonify({
                    "success": False,
                    "message": "Compte désactivé"
                }), 403

            # Générer le token
            token = generer_token(user['id'], user['role'], user['entreprise_id'])

            logger.info(f"Connexion réussie: {email}")

            return jsonify({
                "success": True,
                "token": token,
                "user": {
                    "id": user['id'],
                    "nom": user['nom'],
                    "email": user['email'],
                    "role": user['role'],
                    "entreprise_id": user['entreprise_id']
                }
            }), 200

        except Exception as e:
            logger.error(f"Erreur connexion: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500

    @app.route("/api/auth/me", methods=["GET"])
    def get_current_user_core():
        """Récupère le profil de l'utilisateur courant"""
        try:
            user_id = request.user_id  # Du middleware d'authentification
            
            user = DatabaseService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404

            return jsonify({
                "success": True,
                "user": {
                    "id": user['id'],
                    "nom": user['nom'],
                    "email": user['email'],
                    "role": user['role'],
                    "telephone": user.get('telephone', ''),
                    "entreprise_id": user['entreprise_id']
                }
            }), 200

        except Exception as e:
            logger.error(f"Erreur get_current_user: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500
