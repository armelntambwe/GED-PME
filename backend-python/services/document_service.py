# services/document_service.py
# Service de gestion des documents - Logique métier

import os
from datetime import datetime

from extensions import db
from models.document import Document
from models.log import Log
from models_sqlalchemy import Document as DocumentModel
from services.indexation_service import IndexationService
from services.version_service import VersionService
from services.category_service import CategoryService
from utils.file_upload import allowed_file, secure_filename_with_path
from utils.ocr_helper import extract_text_from_file
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH


class DocumentService:
    """Service de gestion des documents - Upload, téléchargement, CRUD"""

    @staticmethod
    def _run_ocr_and_index(doc_id):
        document = DocumentModel.query.get(doc_id)
        if not document or not document.fichier_chemin:
            return

        texte, erreur = extract_text_from_file(document.fichier_chemin)
        if texte and not erreur:
            document.contenu_ocr = texte
            db.session.commit()
            IndexationService.index_document(
                doc_id,
                titre=document.titre,
                description=document.description,
                contenu_ocr=texte,
            )

    @staticmethod
    def upload_file(file, titre, description, auteur_id, categorie_id=None, entreprise_id=None, auteur_role=None):
        if not file:
            return False, "Aucun fichier fourni", None
        if file.filename == '':
            return False, "Nom de fichier vide", None
        if not allowed_file(file.filename):
            return False, "Format non autorisé (PDF, DOCX, JPG, PNG, TXT)", None
        if categorie_id and not CategoryService.belongs_to_entreprise(categorie_id, entreprise_id):
            return False, "Catégorie invalide pour votre entreprise", None

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_CONTENT_LENGTH:
            return False, f"Fichier trop volumineux (max {MAX_CONTENT_LENGTH // (1024 * 1024)} Mo)", None

        secure_name = secure_filename_with_path(file.filename, auteur_id)
        filepath = os.path.join(UPLOAD_FOLDER, secure_name)
        file.save(filepath)

        doc_id = Document.create(
            titre=titre,
            description=description,
            fichier_nom=file.filename,
            fichier_chemin=filepath,
            taille=file_size,
            type_mime=file.mimetype,
            auteur_id=auteur_id,
            categorie_id=categorie_id,
            entreprise_id=entreprise_id,
        )

        VersionService.create_initial_version(doc_id, auteur_id)
        Log.create('CREATION', f"Document '{titre}' uploadé", auteur_id, doc_id)

        try:
            DocumentService._run_ocr_and_index(doc_id)
        except Exception:
            pass

        IndexationService.index_document(doc_id, titre=titre, description=description)

        if auteur_role == 'admin_pme':
            Document.auto_publish_by_admin(doc_id, auteur_id)
            Log.create(
                'PUBLICATION',
                f"Document '{titre}' validé et publié automatiquement (admin PME)",
                auteur_id,
                doc_id,
            )
            return True, "Document validé et publié avec succès", doc_id

        return True, "Document uploadé avec succès", doc_id

    @staticmethod
    def get_documents_by_user(user_id, role, entreprise_id=None, limit=100, search=None, statut=None, ocr=None, page=1, categorie_id=None):
        if role == 'employe':
            docs, total = Document.get_by_auteur(
                user_id, search=search, statut=statut, ocr=ocr,
                page=page, limit=limit, entreprise_id=entreprise_id, categorie_id=categorie_id,
            )
        elif role == 'admin_pme':
            docs, total = Document.get_by_entreprise(
                entreprise_id, search=search, statut=statut, ocr=ocr, page=page, limit=limit,
            )
        else:
            docs, total = Document.get_all_paginated(
                limit=limit, search=search, statut=statut, ocr=ocr, page=page,
            )

        limit = max(1, min(limit, 200))
        total_pages = max(1, (total + limit - 1) // limit)
        return docs, total, total_pages

    @staticmethod
    def get_document(doc_id, user_id, role, entreprise_id=None):
        doc = Document.get_by_id(doc_id)
        if not doc:
            return None, "Document non trouvé"

        if role == 'employe':
            if doc['auteur_id'] != user_id:
                return None, "Accès non autorisé"
        elif role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return None, "Accès non autorisé"

        return doc, None

    @staticmethod
    def update_document(doc_id, user_id, data, file=None):
        document = DocumentModel.query.get(doc_id)
        if not document or document.supprime_le is not None:
            return False, "Document non trouvé", None
        if document.auteur_id != user_id:
            return False, "Accès non autorisé", None
        if document.statut not in ('brouillon', 'rejete'):
            return False, "Document non modifiable dans cet état", None

        VersionService.create_snapshot(document, user_id, data.get('commentaire', 'Sauvegarde avant modification'))

        if file and file.filename:
            if not allowed_file(file.filename):
                return False, "Format non autorisé", None
            secure_name = secure_filename_with_path(file.filename, user_id)
            filepath = os.path.join(UPLOAD_FOLDER, secure_name)
            file.save(filepath)
            document.fichier_nom = file.filename
            document.fichier_chemin = filepath
            file.seek(0, os.SEEK_END)
            document.fichier_taille = file.tell()

        if 'titre' in data:
            document.titre = data['titre']
        if 'description' in data:
            document.description = data['description']
        if 'categorie_id' in data:
            new_cat = data['categorie_id']
            if new_cat in (None, '', 0, '0'):
                document.categorie_id = None
            elif not CategoryService.belongs_to_entreprise(new_cat, document.entreprise_id):
                return False, "Catégorie invalide pour votre entreprise", None
            else:
                document.categorie_id = int(new_cat)

        document.version_actuelle = VersionService._next_version_numero(document.id)
        document.date_modification = datetime.utcnow()
        db.session.commit()

        IndexationService.index_document(
            document.id,
            titre=document.titre,
            description=document.description,
            contenu_ocr=document.contenu_ocr,
        )
        Log.create('MODIFICATION', f"Document {doc_id} modifié (v{document.version_actuelle})", user_id, doc_id)
        return True, "Document mis à jour", document.id

    @staticmethod
    def get_corbeille(role, entreprise_id=None):
        if role == 'admin_pme':
            return Document.get_corbeille(entreprise_id)
        return Document.get_corbeille()

    @staticmethod
    def restore_document(doc_id, user_id):
        Document.restore(doc_id)
        Log.create('RESTAURATION', f"Document {doc_id} restauré", user_id, doc_id)
        return True, "Document restauré"

    @staticmethod
    def delete_permanently(doc_id, user_id):
        from utils.file_paths import resolve_document_path
        doc = Document.get_by_id(doc_id)
        if doc and doc.get('fichier_chemin'):
            path = resolve_document_path(doc['fichier_chemin'])
            if path and os.path.exists(path):
                os.remove(path)
        Document.delete_permanently(doc_id)
        Log.create('SUPPRESSION_DEFINITIVE', f"Document {doc_id} supprimé définitivement", user_id, doc_id)
        return True, "Document supprimé définitivement"

    @staticmethod
    def get_evolution(entreprise_id=None, weeks=8):
        return Document.get_evolution(entreprise_id, weeks)

    @staticmethod
    def copy_document(doc_id, user_id, role, entreprise_id=None, categorie_id=None, titre=None):
        """Duplique un document (fichier + métadonnées) en brouillon."""
        import shutil

        doc, error = DocumentService.get_document(doc_id, user_id, role, entreprise_id)
        if error:
            return False, error, None

        from utils.file_paths import resolve_document_path
        source = DocumentModel.query.get(doc_id)
        src_path = resolve_document_path(source.fichier_chemin if source else None)
        if not source or not src_path:
            return False, 'Fichier source introuvable', None

        if role == 'employe' and source.auteur_id != user_id:
            return False, 'Vous ne pouvez copier que vos propres documents', None

        secure_name = secure_filename_with_path(source.fichier_nom or 'document', user_id)
        dest_path = os.path.join(UPLOAD_FOLDER, secure_name)
        shutil.copy2(src_path, dest_path)

        new_titre = titre or f"{source.titre} (copie)"
        target_cat = categorie_id if categorie_id is not None else source.categorie_id
        if target_cat == '' or target_cat == 0:
            target_cat = None
        ent_id = source.entreprise_id or entreprise_id
        if target_cat and not CategoryService.belongs_to_entreprise(target_cat, ent_id):
            return False, 'Catégorie invalide pour votre entreprise', None

        new_id = Document.create(
            titre=new_titre,
            description=source.description,
            fichier_nom=source.fichier_nom,
            fichier_chemin=dest_path,
            taille=source.fichier_taille,
            type_mime=source.type_mime,
            auteur_id=user_id,
            categorie_id=target_cat,
            entreprise_id=source.entreprise_id or entreprise_id,
        )
        VersionService.create_initial_version(new_id, user_id)
        Log.create('COPIE', f"Document {doc_id} copié → {new_id}", user_id, new_id)
        try:
            if source.contenu_ocr:
                new_doc = DocumentModel.query.get(new_id)
                new_doc.contenu_ocr = source.contenu_ocr
                db.session.commit()
            else:
                DocumentService._run_ocr_and_index(new_id)
        except Exception:
            pass
        IndexationService.index_document(new_id, titre=new_titre, description=source.description)
        return True, 'Document copié', new_id
