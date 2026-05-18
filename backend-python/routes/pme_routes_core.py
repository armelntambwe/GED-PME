from flask import request, jsonify
from middleware.auth import token_required, role_required
from services.database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)


def register_pme_routes_core(app):
    @app.route("/api/pme/employes-core", methods=["GET"])
    @token_required
    @role_required(['admin_pme'])
    def pme_employes_core():
        """Récupère les employés de l'entreprise - VERSION SERVICE"""
        try:
            entreprise_id = request.user_entreprise_id

            # Utiliser le service pour récupérer uniquement les employés
            users = DatabaseService.get_users(
                entreprise_id=entreprise_id,
                role='employe'
            )

            return jsonify({
                "success": True,
                "employes": users,
                "count": len(users)
            }), 200

        except Exception as e:
            logger.error(f"Erreur pme_employes_core: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @app.route("/api/pme/stats", methods=["GET"])
    @token_required
    @role_required(['admin_pme'])
    def pme_stats_core():
        """Récupère les statistiques de l'entreprise - VERSION SERVICE"""
        try:
            entreprise_id = request.user_entreprise_id

            stats = DatabaseService.get_stats(entreprise_id)

            return jsonify({
                "success": True,
                "stats": stats
            }), 200

        except Exception as e:
            logger.error(f"Erreur pme_stats: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @app.route("/api/pme/documents", methods=["GET"])
    @token_required
    @role_required(['admin_pme', 'employe'])
    def pme_documents_core():
        """Récupère les documents de l'entreprise - VERSION SERVICE"""
        try:
            entreprise_id = request.user_entreprise_id
            limit = request.args.get("limit", 100, type=int)

            documents = DatabaseService.get_documents(
                entreprise_id=entreprise_id,
                limit=limit
            )

            return jsonify({
                "success": True,
                "documents": documents,
                "count": len(documents)
            }), 200

        except Exception as e:
            logger.error(f"Erreur pme_documents: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
