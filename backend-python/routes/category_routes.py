from flask import request, jsonify
from middleware.auth import token_required, role_required
from services.category_service import CategoryService


def register_category_routes(app):

    @app.route("/categories", methods=["GET"])
    @token_required
    def get_categories():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            categories = CategoryService.get_categories(entreprise_id)
            return jsonify({"success": True, "categories": categories}), 200
        except Exception as e:
            print(f"[ERREUR] get_categories: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/categories", methods=["POST"])
    @token_required
    @role_required(['admin_pme', 'admin_global', 'employe'])
    def create_category():
        try:
            data = request.json or {}
            nom = data.get('nom')
            description = data.get('description', '')
            entreprise_id = getattr(request, 'user_entreprise_id', None)

            if not nom:
                return jsonify({"success": False, "message": "Le nom de la catégorie est requis"}), 400

            category_id = CategoryService.create_category(nom, description, entreprise_id)
            return jsonify({"success": True, "message": "Catégorie créée", "category_id": category_id}), 201
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            print(f"[ERREUR] create_category: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/categories/<int:category_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_pme', 'admin_global', 'employe'])
    def update_category(category_id):
        try:
            data = request.json or {}
            nom = data.get('nom')
            description = data.get('description', '')
            entreprise_id = getattr(request, 'user_entreprise_id', None)

            if not nom:
                return jsonify({"success": False, "message": "Le nom de la catégorie est requis"}), 400

            updated = CategoryService.update_category(category_id, nom, description, entreprise_id)
            if not updated:
                return jsonify({"success": False, "message": "Catégorie non trouvée ou accès non autorisé"}), 404

            return jsonify({"success": True, "message": "Catégorie modifiée"}), 200
        except Exception as e:
            print(f"[ERREUR] update_category: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/categories/<int:category_id>", methods=["DELETE"])
    @token_required
    @role_required(['admin_pme', 'admin_global', 'employe'])
    def delete_category(category_id):
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            deleted = CategoryService.delete_category(category_id, entreprise_id)
            if not deleted:
                return jsonify({"success": False, "message": "Catégorie non trouvée ou accès non autorisé"}), 404
            return jsonify({"success": True, "message": "Catégorie supprimée"}), 200
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            print(f"[ERREUR] delete_category: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
