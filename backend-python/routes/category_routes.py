# routes/category_routes.py
# Routes de gestion des catégories - CRUD

from flask import request, jsonify
from middleware.auth import token_required, role_required
from models.categorie import Categorie

def register_category_routes(app):
    """Enregistre toutes les routes de gestion des catégories"""

    @app.route("/categories", methods=["POST"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def create_category():
        """Crée une nouvelle catégorie"""
        data = request.json
        if not data or "nom" not in data:
            return jsonify({"success": False, "message": "Nom requis"}), 400

        category_id = Categorie.create(data["nom"], data.get("description", ""))

        return jsonify({
            "success": True,
            "message": "Catégorie créée",
            "category_id": category_id
        }), 201

    @app.route("/categories", methods=["GET"])
    @token_required
    def get_categories():
        """Liste toutes les catégories"""
        categories = Categorie.get_all()
        return jsonify({
            "success": True,
            "count": len(categories),
            "categories": categories
        }), 200

    @app.route("/categories/<int:categorie_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def update_category(categorie_id):
        """Modifie une catégorie"""
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Données manquantes"}), 400

        Categorie.update(categorie_id, data.get("nom"), data.get("description"))

        return jsonify({"success": True, "message": "Catégorie modifiée"}), 200

    @app.route("/categories/<int:categorie_id>", methods=["DELETE"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def delete_category(categorie_id):
        """Supprime une catégorie"""
        Categorie.delete(categorie_id)
        return jsonify({"success": True, "message": "Catégorie supprimée"}), 200