# routes/category_routes_core.py (version SQLAlchemy Core)
from flask import request, jsonify
from middleware.auth import token_required, role_required
from extensions import engine
from sqlalchemy import select, insert, or_, func
from models.core_tables import categories


def register_category_routes_core(app):

    # ============================================
    # LIRE les catégories (filtrées par entreprise) - VERSION SQLALCHEMY CORE
    # ============================================
    @app.route("/categories-core", methods=["GET"])
    @token_required
    def get_categories_core():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)

            stmt = select(
                categories.c.id,
                categories.c.nom,
                categories.c.description,
                categories.c.date_creation
            ).where(
                or_(categories.c.entreprise_id == entreprise_id, categories.c.entreprise_id == None)
            ).order_by(categories.c.nom.asc())

            with engine.connect() as conn:
                result = conn.execute(stmt)
                categories_rows = [dict(row) for row in result]

            for cat in categories_rows:
                if cat.get('date_creation'):
                    cat['date_creation'] = str(cat['date_creation'])

            return jsonify({"success": True, "categories": categories_rows}), 200
        except Exception as e:
            print(f"[ERREUR] get_categories_core: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # CRÉER une catégorie (liée à l'entreprise) - VERSION SQLALCHEMY CORE
    # ============================================
    @app.route("/categories-core", methods=["POST"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def create_category_core():
        try:
            data = request.json
            nom = data.get('nom')
            description = data.get('description', '')
            entreprise_id = getattr(request, 'user_entreprise_id', None)

            if not nom:
                return jsonify({"success": False, "message": "Le nom est requis"}), 400

            stmt = insert(categories).values(
                nom=nom,
                description=description,
                date_creation=func.now(),
                entreprise_id=entreprise_id
            )

            with engine.begin() as conn:
                result = conn.execute(stmt)
                category_id = result.inserted_primary_key[0]

            return jsonify({
                "success": True,
                "message": "Catégorie créée avec succès",
                "category_id": category_id
            }), 201
        except Exception as e:
            print(f"[ERREUR] create_category_core: {e}")
            return jsonify({"success": False, "message": str(e)}), 500