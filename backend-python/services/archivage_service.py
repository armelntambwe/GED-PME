from datetime import datetime, timedelta

from extensions import db
from models_sqlalchemy import Document, ArchiveDocument
from models.log import Log


class ArchivageService:
    """Archivage automatique des documents obsolètes."""

    RETENTION_OBSOLETE_DAYS = 30

    @staticmethod
    def marquer_obsolete_auto(document):
        """Passe un document publié en obsolète (règle métier optionnelle)."""
        if document.statut != 'publie':
            return False
        document.statut = 'obsolete'
        document.date_obsolete = datetime.utcnow()
        return True

    @staticmethod
    def archiver_document(document_id, user_id, motif='Archivage automatique'):
        document = Document.query.get(document_id)
        if not document:
            return False, 'Document introuvable'

        existing = ArchiveDocument.query.filter_by(document_id=document_id).first()
        if not existing:
            archive = ArchiveDocument(
                document_id=document_id,
                date_archivage=datetime.utcnow(),
                duree_conservation=365,
                motif=motif,
                archive_par=user_id,
            )
            db.session.add(archive)

        document.statut = 'detruit'
        document.date_detruit = datetime.utcnow()
        db.session.commit()

        Log.create('ARCHIVAGE', f"Document {document_id} archivé et détruit", user_id, document_id)
        return True, 'Document archivé'

    @staticmethod
    def run_auto_archivage(system_user_id=1):
        """Archive automatiquement les documents obsolètes dépassant la rétention."""
        cutoff = datetime.utcnow() - timedelta(days=ArchivageService.RETENTION_OBSOLETE_DAYS)
        docs = Document.query.filter(
            Document.statut == 'obsolete',
            Document.date_obsolete.isnot(None),
            Document.date_obsolete <= cutoff,
            Document.supprime_le.is_(None),
        ).all()

        count = 0
        for doc in docs:
            ok, _ = ArchivageService.archiver_document(doc.id, system_user_id)
            if ok:
                count += 1
        return count
