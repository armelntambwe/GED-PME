# routes/document_routes.py
# Routes de gestion des documents - Upload, téléchargement, CRUD

from flask import request, jsonify, send_file
from middleware.auth import token_required, role_required
from services.document_service import DocumentService
from services.validation_service import ValidationService
from models.document import Document
from config import UPLOAD_FOLDER
import os

def register_document_routes(app):
    """Enregistre toutes les routes de gestion des documents"""

    @app.route("/documents", methods=["GET"])
    @token_required
    def get_documents():
        """Liste des documents accessibles"""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        try:
            documents = DocumentService.get_documents_by_user(user_id, role, entreprise_id)

            for doc in documents:
                if doc.get('date_creation'):
                    doc['date_creation'] = str(doc['date_creation'])

            return jsonify({
                "success": True,
                "count": len(documents),
                "documents": documents
            }), 200
        except Exception as e:
            print(f"[ERREUR] get_documents: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/documents/upload", methods=["POST"])
    @token_required
    def upload_document():
        """Upload d'un fichier"""
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "Aucun fichier"}), 400

        file = request.files['file']
        titre = request.form.get('titre', file.filename)
        description = request.form.get('description', '')
        categorie_id = request.form.get('categorie_id')
        user_id = request.user_id
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        success, message, doc_id = DocumentService.upload_file(
            file, titre, description, user_id, categorie_id, entreprise_id
        )

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({
            "success": True,
            "message": message,
            "document_id": doc_id
        }), 201

    @app.route("/documents/<int:doc_id>/download", methods=["GET"])
    @token_required
    def download_document(doc_id):
        """Téléchargement d'un fichier"""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc, error = DocumentService.get_document(doc_id, user_id, role, entreprise_id)

        if error:
            return jsonify({"success": False, "message": error}), 403

        if not doc or not doc.get('fichier_chemin'):
            return jsonify({"success": False, "message": "Fichier introuvable"}), 404

        if not os.path.exists(doc['fichier_chemin']):
            return jsonify({"success": False, "message": "Fichier introuvable"}), 404

        return send_file(
            doc['fichier_chemin'],
            as_attachment=True,
            download_name=doc.get('fichier_nom', 'document')
        )

    @app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
    @token_required
    def soumettre_document(doc_id):
        """Soumet un document pour validation"""
        user_id = request.user_id

        success, message = ValidationService.soumettre(doc_id, user_id)

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/valider", methods=["PUT"])
    @token_required
    @role_required(['admin_pme'])
    def valider_document(doc_id):
        """Valide un document soumis"""
        user_id = request.user_id
        role = request.user_role

        success, message = ValidationService.valider(doc_id, user_id, role)

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
    @token_required
    @role_required(['admin_pme'])
    def rejeter_document(doc_id):
        """Rejette un document soumis"""
        data = request.json
        if not data or "commentaire" not in data:
            return jsonify({"success": False, "message": "Commentaire requis"}), 400

        user_id = request.user_id
        role = request.user_role
        commentaire = data["commentaire"]

        success, message = ValidationService.rejeter(doc_id, user_id, role, commentaire)

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/supprimer", methods=["DELETE"])
    @token_required
    def supprimer_document(doc_id):
        """Déplace le document vers la corbeille (soft delete)"""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc = Document.get_by_id(doc_id)
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404

        if role == 'employe' and doc['auteur_id'] != user_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403
        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        Document.soft_delete(doc_id, user_id)

        return jsonify({"success": True, "message": "Document déplacé vers la corbeille"}), 200

    @app.route("/documents/corbeille", methods=["GET"])
    @token_required
    def get_corbeille():
        """Liste des documents dans la corbeille"""
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        documents = DocumentService.get_corbeille(role, entreprise_id)

        for doc in documents:
            if doc.get('date_suppression'):
                doc['date_suppression'] = str(doc['date_suppression'])

        return jsonify({
            "success": True,
            "documents": documents
        }), 200

    @app.route("/documents/<int:doc_id>/restaurer", methods=["PUT"])
    @token_required
    def restaurer_document(doc_id):
        """Restaure un document depuis la corbeille"""
        user_id = request.user_id

        success, message = DocumentService.restore_document(doc_id, user_id)

        return jsonify({"success": success, "message": message}), 200

    @app.route("/documents/<int:doc_id>/effacer", methods=["DELETE"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def effacer_definitivement(doc_id):
        """Supprime définitivement un document"""
        user_id = request.user_id

        success, message = DocumentService.delete_permanently(doc_id, user_id)

        return jsonify({"success": success, "message": message}), 200

    @app.route("/mes-documents", methods=["GET"])
    @token_required
    def mes_documents():
        """Liste des documents personnels"""
        user_id = request.user_id

        documents = Document.get_by_auteur(user_id)

        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])

        return jsonify({
            "success": True,
            "documents": documents
        }), 200