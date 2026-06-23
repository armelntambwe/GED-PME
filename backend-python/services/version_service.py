import os
import shutil
from datetime import datetime

from extensions import db
from models_sqlalchemy import Document as DocumentModel, VersionDocument


class VersionService:
    """Gestion du versionnage documentaire."""

    @staticmethod
    def _next_version_numero(document_id):
        last = (
            VersionDocument.query.filter_by(document_id=document_id)
            .order_by(VersionDocument.version_numero.desc())
            .first()
        )
        return (last.version_numero + 1) if last else 1

    @staticmethod
    def create_snapshot(document, user_id, commentaire=''):
        """Enregistre l'état courant du document comme nouvelle version."""
        if not document:
            return None

        numero = VersionService._next_version_numero(document.id)
        version = VersionDocument(
            document_id=document.id,
            version_numero=numero,
            titre=document.titre,
            description=document.description,
            fichier_chemin=document.fichier_chemin,
            fichier_nom=document.fichier_nom,
            commentaire=commentaire or f'Version {numero}',
            date_creation=datetime.utcnow(),
            createur_id=user_id,
        )
        db.session.add(version)
        db.session.flush()
        return version

    @staticmethod
    def create_initial_version(document_id, user_id):
        document = DocumentModel.query.get(document_id)
        if not document:
            return None
        existing = VersionDocument.query.filter_by(document_id=document_id).first()
        if existing:
            return existing
        version = VersionDocument(
            document_id=document.id,
            version_numero=1,
            titre=document.titre,
            description=document.description,
            fichier_chemin=document.fichier_chemin,
            fichier_nom=document.fichier_nom,
            commentaire='Version initiale',
            date_creation=document.date_creation or datetime.utcnow(),
            createur_id=user_id,
        )
        db.session.add(version)
        db.session.commit()
        return version

    @staticmethod
    def restore_version(document_id, version_id, user_id):
        """Restaure une version antérieure (snapshot avant restauration)."""
        document = DocumentModel.query.get(document_id)
        version = VersionDocument.query.filter_by(id=version_id, document_id=document_id).first()

        if not document or not version:
            return False, 'Version introuvable'

        if document.statut not in ('brouillon', 'rejete'):
            return False, 'Restauration autorisée uniquement en brouillon ou après rejet'

        VersionService.create_snapshot(document, user_id, 'Sauvegarde avant restauration')

        if version.fichier_chemin and document.fichier_chemin and version.fichier_chemin != document.fichier_chemin:
            if os.path.isfile(version.fichier_chemin):
                shutil.copy2(version.fichier_chemin, document.fichier_chemin)

        document.titre = version.titre or document.titre
        document.description = version.description
        document.fichier_nom = version.fichier_nom or document.fichier_nom
        if version.fichier_chemin:
            document.fichier_chemin = version.fichier_chemin
        document.date_modification = datetime.utcnow()
        db.session.commit()
        return True, f'Version {version.version_numero} restaurée'
