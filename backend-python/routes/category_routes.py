from flask import request, jsonify
from middleware.auth import token_required, role_required
from utils.db import get_db
from datetime import datetime

def register_category_routes(app):

    # ============================================
    # LIRE les catégories (filtrées par entreprise)
    # ============================================
    @app.route("/categories", methods=["GET"])
    @token_required
    def get_categories():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            conn = get_db()
            cur = conn.cursor()
            
            # Récupère les catégories de l'entreprise + éventuellement les catégories globales (entreprise_id IS NULL)
            cur.execute("""
                SELECT id, nom, description, date_creation
                FROM categories
                WHERE entreprise_id = %s OR entreprise_id IS NULL
                ORDER BY nom ASC
            """, (entreprise_id,))
            
            categories = cur.fetchall()
            cur.close()
            conn.close()
            
            # Conversion des dates en string
            for cat in categories:
                if cat.get('date_creation'):
                    cat['date_creation'] = str(cat['date_creation'])
            
            return jsonify({"success": True, "categories": categories}), 200
        except Exception as e:
            print(f"[ERREUR] get_categories: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # CRÉER une catégorie (liée à l'entreprise)
    # ============================================
    @app.route("/categories", methods=["POST"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def create_category():
        try:
            data = request.json
            nom = data.get('nom')
            description = data.get('description', '')
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            
            if not nom:
                return jsonify({"success": False, "message": "Le nom de la catégorie est requis"}), 400
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO categories (nom, description, entreprise_id, date_creation)
                VALUES (%s, %s, %s, %s)
            """, (nom, description, entreprise_id, datetime.now()))
            
            category_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Catégorie créée", "category_id": category_id}), 201
        except Exception as e:
            print(f"[ERREUR] create_category: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # MODIFIER une catégorie (vérification appartenance)
    # ============================================
    @app.route("/categories/<int:category_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def update_category(category_id):
        try:
            data = request.json
            nom = data.get('nom')
            description = data.get('description', '')
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            
            if not nom:
                return jsonify({"success": False, "message": "Le nom de la catégorie est requis"}), 400
            
            conn = get_db()
            cur = conn.cursor()
            
            # Vérifier que la catégorie appartient bien à l'entreprise
            cur.execute("""
                SELECT id FROM categories
                WHERE id = %s AND (entreprise_id = %s OR entreprise_id IS NULL)
            """, (category_id, entreprise_id))
            
            if not cur.fetchone():
                cur.close()
                conn.close()
                return jsonify({"success": False, "message": "Catégorie non trouvée ou accès non autorisé"}), 404
            
            cur.execute("""
                UPDATE categories
                SET nom = %s, description = %s
                WHERE id = %s
            """, (nom, description, category_id))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Catégorie modifiée"}), 200
        except Exception as e:
            print(f"[ERREUR] update_category: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # SUPPRIMER une catégorie (vérification appartenance)
    # ============================================
    @app.route("/categories/<int:category_id>", methods=["DELETE"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def delete_category(category_id):
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            conn = get_db()
            cur = conn.cursor()
            
            # Vérifier que la catégorie appartient bien à l'entreprise
            cur.execute("""
                SELECT id FROM categories
                WHERE id = %s AND (entreprise_id = %s OR entreprise_id IS NULL)
            """, (category_id, entreprise_id))
            
            if not cur.fetchone():
                cur.close()
                conn.close()
                return jsonify({"success": False, "message": "Catégorie non trouvée ou accès non autorisé"}), 404
            
            cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Catégorie supprimée"}), 200
        except Exception as e:
            print(f"[ERREUR] delete_category: {e}")
            return jsonify({"success": False, "message": str(e)}), 500