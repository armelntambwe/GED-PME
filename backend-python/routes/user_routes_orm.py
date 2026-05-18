"""
Routes utilisateur refactorisées - ORM SQLAlchemy pur (sans SQL brut)
Remplace progressivement user_routes.py
"""

from flask import request, jsonify
from middleware.auth import token_required, role_required
from services.user_service import UserService
from models_sqlalchemy import User
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)


def register_user_routes_orm(app):
    """Enregistre les routes utilisateur avec services ORM."""
    
    # ============================================
    # LISTER TOUS LES UTILISATEURS
    # ============================================
    
    @app.route("/api/users-orm", methods=["GET"])
    @token_required
    def get_users_orm():
        """Récupère la liste des utilisateurs."""
        try:
            limit = request.args.get('limit', 100, type=int)
            users = UserService.get_users(limit=limit)
            
            return jsonify({"success": True, "count": len(users), "users": users}), 200
        except Exception as e:
            logger.error(f"Erreur get_users_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # LISTER LES EMPLOYÉS D'UNE ENTREPRISE
    # ============================================
    
    @app.route("/api/admin/employes-orm", methods=["GET"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def get_employes_orm():
        """Récupère la liste des employés de l'entreprise."""
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            limit = request.args.get('limit', 100, type=int)
            
            if entreprise_id is None:
                return jsonify({
                    "success": False,
                    "message": "Entreprise non identifiée"
                }), 400
            
            employes = UserService.get_users(
                entreprise_id=entreprise_id,
                role='employe',
                limit=limit
            )
            
            return jsonify({
                "success": True,
                "count": len(employes),
                "employes": employes
            }), 200
        except Exception as e:
            logger.error(f"Erreur get_employes_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # CRÉER UN EMPLOYÉ
    # ============================================
    
    @app.route("/api/admin/employes-orm", methods=["POST"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def create_employe_orm():
        """Crée un nouvel employé dans l'entreprise."""
        try:
            data = request.json
            
            # Validation des données
            nom = data.get('nom', '').strip()
            email = data.get('email', '').strip()
            telephone = data.get('telephone', '').strip()
            password = data.get('password', 'employe123')
            
            if not nom or not email:
                return jsonify({
                    "success": False,
                    "message": "Le nom et l'email sont requis"
                }), 400
            
            if len(password) < 6:
                return jsonify({
                    "success": False,
                    "message": "Le mot de passe doit avoir au moins 6 caractères"
                }), 400
            
            # Vérifier que l'email n'existe pas
            existing_user = UserService.get_user_by_email(email)
            if existing_user:
                return jsonify({
                    "success": False,
                    "message": "Cet email est déjà utilisé"
                }), 409
            
            # Créer le nouvel employé
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
            
            return jsonify({
                "success": True,
                "message": "Employé créé avec succès",
                "user_id": user_id,
                "email": email,
                "password": password
            }), 201
        except Exception as e:
            logger.error(f"Erreur create_employe_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # DÉSACTIVER UN UTILISATEUR
    # ============================================
    
    @app.route("/api/users/<int:user_id>/desactiver-orm", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def desactiver_user_orm(user_id):
        """Désactive un utilisateur."""
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404
            
            UserService.update_user_status(user_id, False)
            
            return jsonify({
                "success": True,
                "message": f"Utilisateur {user['nom']} désactivé",
                "user_id": user_id
            }), 200
        except Exception as e:
            logger.error(f"Erreur desactiver_user_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # RÉACTIVER UN UTILISATEUR
    # ============================================
    
    @app.route("/api/users/<int:user_id>/reactiver-orm", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def reactiver_user_orm(user_id):
        """Réactive un utilisateur."""
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404
            
            UserService.update_user_status(user_id, True)
            
            return jsonify({
                "success": True,
                "message": f"Utilisateur {user['nom']} réactivé",
                "user_id": user_id
            }), 200
        except Exception as e:
            logger.error(f"Erreur reactiver_user_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # SUPPRIMER UN UTILISATEUR
    # ============================================
    
    @app.route("/api/users/<int:user_id>/delete-orm", methods=["DELETE"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def delete_user_orm(user_id):
        """Supprime un utilisateur."""
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404
            
            UserService.delete_user(user_id)
            
            return jsonify({
                "success": True,
                "message": f"Utilisateur {user['nom']} supprimé",
                "user_id": user_id
            }), 200
        except Exception as e:
            logger.error(f"Erreur delete_user_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # RECHERCHER DES UTILISATEURS
    # ============================================
    
    @app.route("/api/users/search-orm", methods=["GET"])
    @token_required
    def search_users_orm():
        """Recherche des utilisateurs par nom ou email."""
        try:
            search_term = request.args.get('q', '').strip()
            limit = request.args.get('limit', 50, type=int)
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            
            if not search_term or len(search_term) < 2:
                return jsonify({
                    "success": False,
                    "message": "Minimum 2 caractères pour la recherche"
                }), 400
            
            results = UserService.search_users(
                search_term=search_term,
                entreprise_id=entreprise_id,
                limit=limit
            )
            
            return jsonify({
                "success": True,
                "count": len(results),
                "results": results
            }), 200
        except Exception as e:
            logger.error(f"Erreur search_users_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # OBTENIR LE PROFIL DE L'UTILISATEUR ACTUEL
    # ============================================
    
    @app.route("/api/me-orm", methods=["GET"])
    @token_required
    def get_current_user_orm():
        """Récupère le profil de l'utilisateur actuellement connecté."""
        try:
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non authentifié"
                }), 401
            
            user = UserService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404
            
            return jsonify({
                "success": True,
                "user": user
            }), 200
        except Exception as e:
            logger.error(f"Erreur get_current_user_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    # ============================================
    # METTRE À JOUR LE PROFIL DE L'UTILISATEUR
    # ============================================
    
    @app.route("/api/me-orm", methods=["PUT"])
    @token_required
    def update_current_user_orm():
        """Met à jour le profil de l'utilisateur actuellement connecté."""
        try:
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non authentifié"
                }), 401
            
            data = request.json
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404
            
            # Mettre à jour les champs autorisés
            if 'nom' in data:
                user.nom = data['nom'].strip()
            if 'telephone' in data:
                user.telephone = data.get('telephone', '').strip()
            
            from extensions import db
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Profil mis à jour",
                "user": user.to_dict()
            }), 200
        except Exception as e:
            logger.error(f"Erreur update_current_user_orm: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
