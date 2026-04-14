# services/document_service.py
# Service de gestion des documents - Logique métier

import os
from models.document import Document
from models.log import Log
from models.notification import Notification
from utils.file_upload import allowed_file, secure_filename_with_path
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH

class DocumentService:
    """Service de gestion des documents - Upload, téléchargement, CRUD"""

    @staticmethod
    def upload_file(file, titre, description, auteur_id, categorie_id=None, entreprise_id=None):
        """
        Upload d'un fichier
        Retourne: (success, message, document_id)
        """
        # Vérification du fichier
        if not file:
            return False, "Aucun fichier fourni", None

        if file.filename == '':
            return False, "Nom de fichier vide", None

        if not allowed_file(file.filename):
            return False, "Format non autorisé (PDF, DOCX, JPG, PNG, TXT)", None

        # Vérification de la taille
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_CONTENT_LENGTH:
            return False, f"Fichier trop volumineux (max {MAX_CONTENT_LENGTH // (1024*1024)} Mo)", None

        # Sauvegarde sécurisée du fichier
        secure_name = secure_filename_with_path(file.filename, auteur_id)
        filepath = os.path.join(UPLOAD_FOLDER, secure_name)
        file.save(filepath)

        # Enregistrement en base de données
        doc_id = Document.create(
            titre=titre,
            description=description,
            fichier_nom=file.filename,
            fichier_chemin=filepath,
            taille=file_size,
            type_mime=file.mimetype,
            auteur_id=auteur_id,
            categorie_id=categorie_id,
            entreprise_id=entreprise_id
        )

        # Journalisation
        Log.create('CREATION', f"Document '{titre}' uploadé", auteur_id, doc_id)

        return True, "Document uploadé avec succès", doc_id

    @staticmethod
    def get_documents_by_user(user_id, role, entreprise_id=None):
        """
        Récupère les documents selon le rôle de l'utilisateur
        - Employé : ses propres documents
        - Admin PME : documents de son entreprise
        - Admin Global : tous les documents
        """
        if role == 'employe':
            return Document.get_by_auteur(user_id)
        elif role == 'admin_pme':
            return Document.get_by_entreprise(entreprise_id)
        else:  # admin_global
            return Document.get_all()

    @staticmethod
    def get_document(doc_id, user_id, role, entreprise_id=None):
        """
        Récupère un document avec vérification des droits d'accès
        Retourne: (document, error_message)
        """
        doc = Document.get_by_id(doc_id)

        if not doc:
            return None, "Document non trouvé"

        # Vérification des droits
        if role == 'employe' and doc['auteur_id'] != user_id:
            return None, "Accès non autorisé"

        if role == 'admin_pme' and doc.get('entreprise_id') != entreprise_id:
            return None, "Accès non autorisé"

        return doc, None

    @staticmethod
    def search_documents(keyword, role, user_id, entreprise_id=None):
        """Recherche des documents par mot-clé"""
        # Implémentation à venir
        pass

    @staticmethod
    def get_corbeille(role, entreprise_id=None):
        """Récupère les documents dans la corbeille"""
        if role == 'admin_pme':
            return Document.get_corbeille(entreprise_id)
        else:
            return Document.get_corbeille()

    @staticmethod
    def restore_document(doc_id, user_id):
        """Restaure un document depuis la corbeille"""
        Document.restore(doc_id)
        Log.create('RESTAURATION', f"Document {doc_id} restauré", user_id, doc_id)
        return True, "Document restauré"

    @staticmethod
    def delete_permanently(doc_id, user_id):
        """Supprime définitivement un document"""
        # Récupérer et supprimer le fichier physique
        doc = Document.get_by_id(doc_id)
        if doc and doc.get('fichier_chemin') and os.path.exists(doc['fichier_chemin']):
            os.remove(doc['fichier_chemin'])

        # Supprimer l'entrée en base
        Document.delete_permanently(doc_id)
        Log.create('SUPPRESSION_DEFINITIVE', f"Document {doc_id} supprimé définitivement", user_id, doc_id)
        return True, "Document supprimé définitivement"

    @staticmethod
    def get_evolution(entreprise_id=None, weeks=8):
        """Récupère l'évolution des documents sur N semaines"""
        return Document.get_evolution(entreprise_id, weeks)