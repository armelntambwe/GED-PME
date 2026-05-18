# routes/admin_routes_core.py
"""
Routes administrateur utilisant DatabaseService (version SQLAlchemy Core)
Gestion des utilisateurs, réinitialisation de mots de passe, .
Remplace progressivement admin_routes.py
"""

from flask import request, jsonify
from werkzeug.security import generate_password_hash
from middleware.auth import token_required, role_required
from services.database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)


def register_admin_routes_core(app):
    """Enregistre les routes administrateur avec DatabaseService."""

    @app.route("/api/admin/users", methods=["GET"])
    @token_required
    @role_required(["admin", "admin_pme"])
    def list_users_core():
        """Récupère la liste des utilisateurs - VERSION SERVICE"""
        try:
            entreprise_id = request.args.get("entreprise_id", type=int)
            role = request.args.get("role")
            limit = request.args.get("limit", 100, type=int)

            users = DatabaseService.get_users(
                entreprise_id=entreprise_id,
                role=role,
                limit=limit
            )

            return jsonify({
                "success": True,
                "count": len(users),
                "users": users
            }), 200

        except Exception as e:
            logger.error(f"Erreur list_users: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500

    @app.route("/api/admin/users/<int:user_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(["admin", "admin_pme"])
    def toggle_user_core(user_id):
        """Active/désactive un utilisateur - VERSION SERVICE"""
        try:
            # Récupérer l'utilisateur actuel
            user = DatabaseService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404

            # Inverser le statut
            new_status = not user['actif']
            DatabaseService.update_user_status(user_id, new_status)

            logger.info(f"Utilisateur {user_id} toggled to {new_status}")

            return jsonify({
                "success": True,
                "message": f"Utilisateur {'activé' if new_status else 'désactivé'}",
                "user_id": user_id,
                "actif": new_status
            }), 200

        except Exception as e:
            logger.error(f"Erreur toggle_user: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500

    @app.route("/api/admin/users/<int:user_id>/reset-password", methods=["POST"])
    @token_required
    @role_required(["admin", "admin_pme"])
    def reset_user_password_core(user_id):
        """Réinitialise le mot de passe d'un utilisateur - VERSION SERVICE"""
        try:
            data = request.json or {}
            new_password = data.get("password")

            if not new_password or len(new_password) < 6:
                return jsonify({
                    "success": False,
                    "message": "Mot de passe requis (minimum 6 caractères)"
                }), 400

            # Vérifier que l'utilisateur existe
            user = DatabaseService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404

            # Hacher et enregistrer
            password_hash = generate_password_hash(new_password)
            DatabaseService.reset_user_password(user_id, password_hash)

            logger.info(f"Mot de passe réinitialisé pour l'utilisateur {user_id}")

            return jsonify({
                "success": True,
                "message": "Mot de passe réinitialisé avec succès",
                "user_id": user_id
            }), 200

        except Exception as e:
            logger.error(f"Erreur reset_user_password: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500

    @app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
    @token_required
    @role_required(["admin", "admin_pme"])
    def delete_user_core(user_id):
        """Supprime un utilisateur - VERSION SERVICE"""
        try:
            user = DatabaseService.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }), 404

            # Soft delete (marquer comme inactif) plutôt que suppression physique
            DatabaseService.update_user_status(user_id, False)

            logger.info(f"Utilisateur {user_id} supprimé (soft delete)")

            return jsonify({
                "success": True,
                "message": "Utilisateur supprimé",
                "user_id": user_id
            }), 200

        except Exception as e:
            logger.error(f"Erreur delete_user: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500

    @app.route("/api/admin/stats", methods=["GET"])
    @token_required
    @role_required(["admin", "admin_pme"])
    def get_admin_stats_core():
        """Récupère les statistiques globales - VERSION SERVICE"""
        try:
            entreprise_id = request.args.get("entreprise_id", type=int)

            stats = DatabaseService.get_stats(entreprise_id)

            return jsonify({
                "success": True,
                "stats": stats
            }), 200

        except Exception as e:
            logger.error(f"Erreur get_admin_stats: {e}")
            return jsonify({
                "success": False,
                "message": f"Erreur serveur: {str(e)}"
            }), 500
