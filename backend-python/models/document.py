from datetime import datetime
from extensions import db
from models_sqlalchemy import Document as DocumentModel

class Document:
    """Classe modèle pour les documents"""

    @staticmethod
    def create(titre, description, fichier_nom, fichier_chemin, taille, type_mime, auteur_id, categorie_id=None, entreprise_id=None):
        document = DocumentModel(
            titre=titre,
            description=description,
            fichier_nom=fichier_nom,
            fichier_chemin=fichier_chemin,
            fichier_taille=taille,
            type_mime=type_mime,
            auteur_id=auteur_id,
            statut='brouillon',
            categorie_id=categorie_id,
            entreprise_id=entreprise_id
        )
        db.session.add(document)
        db.session.commit()
        return document.id

    @staticmethod
    def get_by_id(doc_id):
        document = DocumentModel.query.get(doc_id)
        return document.to_dict() if document else None

    @staticmethod
    def get_by_auteur(auteur_id):
        documents = (
            DocumentModel.query
            .filter_by(auteur_id=auteur_id)
            .filter(DocumentModel.supprime_le.is_(None))
            .order_by(DocumentModel.date_creation.desc())
            .all()
        )
        return [doc.to_dict() for doc in documents]

    @staticmethod
    def get_by_entreprise(entreprise_id):
        documents = (
            DocumentModel.query
            .filter_by(entreprise_id=entreprise_id)
            .filter(DocumentModel.supprime_le.is_(None))
            .order_by(DocumentModel.date_creation.desc())
            .all()
        )
        return [doc.to_dict() for doc in documents]

    @staticmethod
    def get_all(limit=100):
        documents = (
            DocumentModel.query
            .filter(DocumentModel.supprime_le.is_(None))
            .order_by(DocumentModel.date_creation.desc())
            .limit(limit)
            .all()
        )
        return [doc.to_dict() for doc in documents]

    @staticmethod
    def get_by_status(status, entreprise_id=None):
        query = DocumentModel.query.filter_by(statut=status).filter(DocumentModel.supprime_le.is_(None))
        if entreprise_id is not None:
            query = query.filter_by(entreprise_id=entreprise_id)
        documents = query.order_by(DocumentModel.date_creation.desc()).all()
        return [doc.to_dict() for doc in documents]

    @staticmethod
    def update_status(doc_id, status, validateur_id=None, commentaire=None):
        document = DocumentModel.query.get(doc_id)
        if not document:
            return False
        document.statut = status
        if status == 'valide':
            document.validateur_id = validateur_id
            document.date_validation = datetime.utcnow()
        elif status == 'rejete':
            document.validateur_id = validateur_id
            document.commentaire_rejet = commentaire
        db.session.commit()
        return True

    @staticmethod
    def soft_delete(doc_id, user_id):
        document = DocumentModel.query.get(doc_id)
        if not document:
            return False
        document.supprime_le = datetime.utcnow()
        document.supprime_par = user_id
        db.session.commit()
        return True

    @staticmethod
    def restore(doc_id):
        document = DocumentModel.query.get(doc_id)
        if not document:
            return False
        document.supprime_le = None
        document.supprime_par = None
        db.session.commit()
        return True

    @staticmethod
    def get_corbeille(entreprise_id=None):
        query = DocumentModel.query.filter(DocumentModel.supprime_le.is_not(None))
        if entreprise_id is not None:
            query = query.filter_by(entreprise_id=entreprise_id)
        documents = query.order_by(DocumentModel.supprime_le.desc()).all()
        return [
            {
                'id': doc.id,
                'titre': doc.titre,
                'date_suppression': doc.supprime_le.isoformat() if doc.supprime_le else None
            }
            for doc in documents
        ]

    @staticmethod
    def delete_permanently(doc_id):
        document = DocumentModel.query.get(doc_id)
        if not document:
            return False
        db.session.delete(document)
        db.session.commit()
        return True

    @staticmethod
    def get_evolution(entreprise_id=None, weeks=8):
        from sqlalchemy import func

        query = db.session.query(
            func.date_format(DocumentModel.date_creation, '%Y-%m-%d').label('date_jour'),
            func.count().label('total')
        )
        if entreprise_id is not None:
            query = query.filter(DocumentModel.entreprise_id == entreprise_id)
        query = query.filter(DocumentModel.date_creation >= func.date_sub(func.now(), func.interval(weeks, 'WEEK')))
        query = query.group_by(func.date_format(DocumentModel.date_creation, '%Y-%m-%d'))
        query = query.order_by('date_jour')
        results = query.all()
        return [{'date_jour': row.date_jour, 'total': row.total} for row in results]
