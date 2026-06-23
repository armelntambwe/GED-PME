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
        limit = request.args.get('limit', 100, type=int)
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search')
        statut = request.args.get('statut')
        ocr = request.args.get('ocr')
        categorie_id = request.args.get('categorie_id')

        try:
            documents, total, total_pages = DocumentService.get_documents_by_user(
                user_id, role, entreprise_id,
                limit=limit, search=search, statut=statut, ocr=ocr, page=page,
                categorie_id=categorie_id,
            )

            for doc in documents:
                if doc.get('date_creation'):
                    doc['date_creation'] = str(doc['date_creation'])

            return jsonify({
                "success": True,
                "count": len(documents),
                "total": total,
                "total_pages": total_pages,
                "page": page,
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
        if categorie_id in (None, '', '0', 0):
            categorie_id = None
        else:
            try:
                categorie_id = int(categorie_id)
            except (TypeError, ValueError):
                categorie_id = None
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

        from utils.file_paths import resolve_document_path, guess_mime
        filepath = resolve_document_path(doc.get('fichier_chemin'))
        if not filepath:
            return jsonify({"success": False, "message": "Fichier introuvable sur le serveur"}), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=doc.get('fichier_nom', 'document'),
            mimetype=guess_mime(doc.get('fichier_nom'), doc.get('type_mime')),
        )

    @app.route("/documents/<int:doc_id>/preview", methods=["GET"])
    @token_required
    def preview_document(doc_id):
        """Aperçu inline du fichier (PDF, images)."""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc, error = DocumentService.get_document(doc_id, user_id, role, entreprise_id)
        if error:
            return jsonify({"success": False, "message": error}), 403

        from utils.file_paths import resolve_document_path, guess_mime
        filepath = resolve_document_path(doc.get('fichier_chemin') if doc else None)
        if not doc or not filepath:
            return jsonify({"success": False, "message": "Fichier introuvable sur le serveur"}), 404

        return send_file(
            filepath,
            as_attachment=False,
            download_name=doc.get('fichier_nom', 'document'),
            mimetype=guess_mime(doc.get('fichier_nom'), doc.get('type_mime')),
        )

    @app.route("/documents/<int:doc_id>/envoyer-email", methods=["POST"])
    @token_required
    def envoyer_document_email(doc_id):
        """Envoie le document en pièce jointe par email."""
        from utils.email_helper import send_document_email

        data = request.json or {}
        email = (data.get('email') or '').strip()
        if not email:
            return jsonify({"success": False, "message": "Email destinataire requis"}), 400

        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)
        doc, error = DocumentService.get_document(doc_id, user_id, role, entreprise_id)
        if error:
            return jsonify({"success": False, "message": error}), 403

        sujet = data.get('sujet') or f"Document GED-PME : {doc.get('titre', 'Document')}"
        message = data.get('message') or f"Veuillez trouver ci-joint le document « {doc.get('titre')} »."
        ok, msg = send_document_email(
            email, sujet, message,
            doc['fichier_chemin'], doc.get('fichier_nom', 'document')
        )
        if not ok:
            return jsonify({"success": False, "message": msg, "smtp_required": True}), 503
        return jsonify({"success": True, "message": msg}), 200

    @app.route("/documents/<int:doc_id>/copier", methods=["POST"])
    @token_required
    def copier_document(doc_id):
        """Duplique un document."""
        data = request.json or {}
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)
        ok, msg, new_id = DocumentService.copy_document(
            doc_id, user_id, role, entreprise_id,
            categorie_id=data.get('categorie_id'),
            titre=data.get('titre'),
        )
        if not ok:
            return jsonify({"success": False, "message": msg}), 400
        return jsonify({"success": True, "message": msg, "document_id": new_id}), 201

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
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc = Document.get_by_id(doc_id)
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        success, message = ValidationService.valider(doc_id, user_id, role)

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
    @token_required
    @role_required(['admin_pme'])
    def rejeter_document(doc_id):
        """Rejette un document soumis"""
        data = request.json or {}
        commentaire = data.get("commentaire") or data.get("motif")
        if not commentaire:
            return jsonify({"success": False, "message": "Commentaire requis"}), 400

        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc = Document.get_by_id(doc_id)
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        success, message = ValidationService.rejeter(doc_id, user_id, role, commentaire)

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/reprendre-brouillon", methods=["PUT"])
    @token_required
    def reprendre_brouillon_document(doc_id):
        """Rejeté → Brouillon"""
        success, message = ValidationService.reprendre_brouillon(doc_id, request.user_id)
        if not success:
            return jsonify({"success": False, "message": message}), 400
        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/publier", methods=["PUT"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def publier_document(doc_id):
        """Validé → Publié"""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc = Document.get_by_id(doc_id)
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        success, message = ValidationService.publier(doc_id, user_id, role)
        if not success:
            return jsonify({"success": False, "message": message}), 400
        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/marquer-obsolete", methods=["PUT"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def marquer_obsolete_document(doc_id):
        """Publié → Obsolète"""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc = Document.get_by_id(doc_id)
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        success, message = ValidationService.marquer_obsolete(doc_id, user_id, role)
        if not success:
            return jsonify({"success": False, "message": message}), 400
        return jsonify({"success": True, "message": message}), 200

    @app.route("/documents/<int:doc_id>/detruire", methods=["PUT"])
    @token_required
    @role_required(['admin_pme', 'admin_global'])
    def detruire_document(doc_id):
        """Obsolète → Détruit (archivage)"""
        user_id = request.user_id
        role = request.user_role
        entreprise_id = getattr(request, 'user_entreprise_id', None)

        doc = Document.get_by_id(doc_id)
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return jsonify({"success": False, "message": "Accès non autorisé"}), 403

        success, message = ValidationService.detruire(doc_id, user_id, role)
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

        documents = Document.get_by_auteur_simple(user_id)

        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])

        return jsonify({
            "success": True,
            "documents": documents
        }), 200