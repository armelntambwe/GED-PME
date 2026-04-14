# services/validation_service.py
# Service de validation - Logique métier du workflow documentaire

from models.document import Document
from models.log import Log
from models.notification import Notification

class ValidationService:
    """Service de validation - Gère le workflow (soumission, validation, rejet)"""

    @staticmethod
    def soumettre(doc_id, user_id):
        """
        Soumet un document pour validation
        Un document ne peut être soumis que s'il est en statut 'brouillon'
        Retourne: (success, message)
        """
        doc = Document.get_by_id(doc_id)

        if not doc:
            return False, "Document non trouvé"

        if doc['auteur_id'] != user_id:
            return False, "Vous ne pouvez soumettre que vos propres documents"

        if doc['statut'] != 'brouillon':
            return False, f"Impossible de soumettre un document en statut '{doc['statut']}'"

        # Mise à jour du statut
        Document.update_status(doc_id, 'soumis')

        # Journalisation
        Log.create('SOUMISSION', f"Document {doc_id} soumis pour validation", user_id, doc_id)

        # Notifier l'admin PME
        if doc.get('entreprise_id'):
            Notification.send_to_admins(
                doc['entreprise_id'],
                'DOCUMENT_SOUMIS',
                f"Un nouveau document '{doc['titre']}' a été soumis pour validation",
                f"/documents/{doc_id}"
            )

        return True, "Document soumis avec succès"

    @staticmethod
    def valider(doc_id, validateur_id, role):
        """
        Valide un document soumis
        Seul un administrateur (PME ou Global) peut valider
        Retourne: (success, message)
        """
        if role not in ['admin_pme', 'admin_global']:
            return False, "Vous n'avez pas les droits pour valider des documents"

        doc = Document.get_by_id(doc_id)

        if not doc:
            return False, "Document non trouvé"

        if doc['statut'] != 'soumis':
            return False, f"Impossible de valider un document en statut '{doc['statut']}'"

        # Mise à jour du statut
        Document.update_status(doc_id, 'valide', validateur_id)

        # Journalisation
        Log.create('VALIDATION', f"Document {doc_id} validé par {validateur_id}", validateur_id, doc_id)

        # Notifier l'auteur
        Notification.create(
            doc['auteur_id'],
            'DOCUMENT_VALIDE',
            f"✅ Votre document '{doc['titre']}' a été validé",
            f"/documents/{doc_id}"
        )

        return True, "Document validé avec succès"

    @staticmethod
    def rejeter(doc_id, validateur_id, role, commentaire):
        """
        Rejette un document soumis avec un commentaire obligatoire
        Seul un administrateur (PME ou Global) peut rejeter
        Retourne: (success, message)
        """
        if role not in ['admin_pme', 'admin_global']:
            return False, "Vous n'avez pas les droits pour rejeter des documents"

        if not commentaire:
            return False, "Un commentaire de rejet est obligatoire"

        doc = Document.get_by_id(doc_id)

        if not doc:
            return False, "Document non trouvé"

        if doc['statut'] != 'soumis':
            return False, f"Impossible de rejeter un document en statut '{doc['statut']}'"

        # Mise à jour du statut avec commentaire
        Document.update_status(doc_id, 'rejete', validateur_id, commentaire)

        # Journalisation
        Log.create('REJET', f"Document {doc_id} rejeté par {validateur_id} : {commentaire}", validateur_id, doc_id)

        # Notifier l'auteur
        Notification.create(
            doc['auteur_id'],
            'DOCUMENT_REJETE',
            f"❌ Votre document '{doc['titre']}' a été rejeté. Motif: {commentaire}",
            f"/documents/{doc_id}"
        )

        return True, "Document rejeté"

    @staticmethod
    def get_documents_en_attente(entreprise_id=None):
        """
        Récupère les documents en attente de validation
        - Admin PME : documents de son entreprise
        - Admin Global : tous les documents
        """
        return Document.get_by_status('soumis', entreprise_id)