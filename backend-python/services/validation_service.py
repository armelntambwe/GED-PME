# services/validation_service.py
# Service de validation - Workflow documentaire complet (7 états)

from models.document import Document
from models.log import Log
from models.notification import Notification
from services.archivage_service import ArchivageService


class ValidationService:
    """Service de validation - Gère le workflow documentaire complet."""

    @staticmethod
    def soumettre(doc_id, user_id):
        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['auteur_id'] != user_id:
            return False, "Vous ne pouvez soumettre que vos propres documents"
        if doc['statut'] != 'brouillon':
            return False, f"Impossible de soumettre un document en statut '{doc['statut']}'"

        Document.update_status(doc_id, 'soumis')
        Log.create('SOUMISSION', f"Document {doc_id} soumis pour validation", user_id, doc_id)

        if doc.get('entreprise_id'):
            Notification.send_to_admins(
                doc['entreprise_id'],
                'DOCUMENT_SOUMIS',
                f"Un nouveau document '{doc['titre']}' a été soumis pour validation",
                f"/documents/{doc_id}",
            )
        return True, "Document soumis avec succès"

    @staticmethod
    def valider(doc_id, validateur_id, role):
        if role != 'admin_pme':
            return False, "Vous n'avez pas les droits pour valider des documents"

        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['statut'] != 'soumis':
            return False, f"Impossible de valider un document en statut '{doc['statut']}'"

        Document.update_status(doc_id, 'valide', validateur_id)
        Log.create('VALIDATION', f"Document {doc_id} validé par {validateur_id}", validateur_id, doc_id)

        msg = f"Votre document '{doc['titre']}' a été validé"
        Notification.create(doc['auteur_id'], 'DOCUMENT_VALIDE', msg, f"/documents/{doc_id}")
        return True, "Document validé avec succès"

    @staticmethod
    def rejeter(doc_id, validateur_id, role, commentaire):
        if role != 'admin_pme':
            return False, "Vous n'avez pas les droits pour rejeter des documents"
        if not commentaire:
            return False, "Un commentaire de rejet est obligatoire"

        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['statut'] != 'soumis':
            return False, f"Impossible de rejeter un document en statut '{doc['statut']}'"

        Document.update_status(doc_id, 'rejete', validateur_id, commentaire)
        Log.create('REJET', f"Document {doc_id} rejeté : {commentaire}", validateur_id, doc_id)

        msg = f"Votre document '{doc['titre']}' a été rejeté. Motif: {commentaire}"
        Notification.create(doc['auteur_id'], 'DOCUMENT_REJETE', msg, f"/documents/{doc_id}")
        return True, "Document rejeté"

    @staticmethod
    def reprendre_brouillon(doc_id, user_id):
        """Rejeté → Brouillon (modification par l'employé)."""
        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['auteur_id'] != user_id:
            return False, "Accès non autorisé"
        if doc['statut'] != 'rejete':
            return False, "Seuls les documents rejetés peuvent repasser en brouillon"

        Document.update_status(doc_id, 'brouillon')
        Log.create('MODIFICATION', f"Document {doc_id} repassé en brouillon", user_id, doc_id)
        return True, "Document repassé en brouillon, vous pouvez le modifier"

    @staticmethod
    def publier(doc_id, user_id, role):
        """Validé → Publié."""
        if role not in ['admin_pme', 'admin_global']:
            return False, "Vous n'avez pas les droits pour publier"

        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['statut'] != 'valide':
            return False, f"Seuls les documents validés peuvent être publiés (statut: {doc['statut']})"

        Document.update_status(doc_id, 'publie', validateur_id=user_id)
        Log.create('PUBLICATION', f"Document {doc_id} publié", user_id, doc_id)

        msg = f"Votre document '{doc['titre']}' est maintenant publié"
        Notification.create(doc['auteur_id'], 'DOCUMENT_PUBLIE', msg, f"/documents/{doc_id}")
        return True, "Document publié avec succès"

    @staticmethod
    def marquer_obsolete(doc_id, user_id, role):
        """Publié → Obsolète."""
        if role not in ['admin_pme', 'admin_global']:
            return False, "Vous n'avez pas les droits pour marquer obsolète"

        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['statut'] != 'publie':
            return False, "Seuls les documents publiés peuvent être marqués obsolètes"

        Document.update_status(doc_id, 'obsolete')
        Log.create('OBSOLESCENCE', f"Document {doc_id} marqué obsolète", user_id, doc_id)
        Notification.create(
            doc['auteur_id'],
            'DOCUMENT_OBSOLETE',
            f"Le document '{doc['titre']}' a été marqué obsolète",
            f"/documents/{doc_id}",
        )
        return True, "Document marqué obsolète"

    @staticmethod
    def detruire(doc_id, user_id, role):
        """Obsolète → Détruit (avec enregistrement d'archive)."""
        if role not in ['admin_pme', 'admin_global']:
            return False, "Vous n'avez pas les droits pour détruire un document"

        doc = Document.get_by_id(doc_id)
        if not doc:
            return False, "Document non trouvé"
        if doc['statut'] != 'obsolete':
            return False, "Seuls les documents obsolètes peuvent être détruits"

        ok, message = ArchivageService.archiver_document(doc_id, user_id, motif='Destruction après obsolescence')
        if not ok:
            return False, message

        Notification.create(
            doc['auteur_id'],
            'DOCUMENT_DETRUIT',
            f"Le document '{doc['titre']}' a été archivé et détruit",
            None,
        )
        return True, "Document archivé et détruit"

    @staticmethod
    def get_documents_en_attente(entreprise_id=None):
        return Document.get_by_status('soumis', entreprise_id)
