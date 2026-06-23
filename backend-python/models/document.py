from datetime import datetime

from sqlalchemy import or_, and_

from extensions import db
from models_sqlalchemy import Document as DocumentModel, Indexation


class Document:
    """Classe modèle pour les documents"""

    ACTIVE_STATUSES_FILTER = DocumentModel.statut != 'detruit'

    @staticmethod
    def _apply_search(query, search=None, ocr=None):
        if search:
            from models_sqlalchemy import User as UserModel
            like = f'%{search.strip()}%'
            query = query.outerjoin(UserModel, DocumentModel.auteur_id == UserModel.id).filter(
                or_(
                    DocumentModel.titre.ilike(like),
                    DocumentModel.description.ilike(like),
                    DocumentModel.contenu_ocr.ilike(like),
                    DocumentModel.fichier_nom.ilike(like),
                    DocumentModel.type_mime.ilike(like),
                    UserModel.nom.ilike(like),
                    UserModel.email.ilike(like),
                )
            ).distinct()
        if ocr:
            ocr_like = f'%{ocr}%'
            query = query.filter(
                or_(
                    DocumentModel.contenu_ocr.ilike(ocr_like),
                    DocumentModel.id.in_(
                        db.session.query(Indexation.document_id).filter(
                            Indexation.mot_cle.ilike(ocr_like)
                        )
                    ),
                )
            )
        return query

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
            entreprise_id=entreprise_id,
            version_actuelle=1,
        )
        db.session.add(document)
        db.session.commit()
        return document.id

    @staticmethod
    def auto_publish_by_admin(doc_id, admin_id):
        """Admin PME : publication directe (validé + publié) sans workflow employé."""
        document = DocumentModel.query.get(doc_id)
        if not document:
            return False
        now = datetime.utcnow()
        document.statut = 'publie'
        document.validateur_id = admin_id
        document.date_validation = now
        document.date_publication = now
        document.workflow_termine = True
        document.date_modification = now
        db.session.commit()
        return True

    @staticmethod
    def get_by_id(doc_id):
        document = DocumentModel.query.get(doc_id)
        if not document or document.statut == 'detruit':
            return None
        return document.to_dict()

    @staticmethod
    def get_by_auteur(auteur_id, search=None, statut=None, ocr=None, page=1, limit=100, entreprise_id=None, categorie_id=None):
        own_docs = DocumentModel.auteur_id == auteur_id
        lecteur_docs = and_(
            DocumentModel.entreprise_id == entreprise_id,
            DocumentModel.statut == 'publie',
        ) if entreprise_id else False

        query = DocumentModel.query.filter(
            DocumentModel.supprime_le.is_(None),
            Document.ACTIVE_STATUSES_FILTER,
        )
        if lecteur_docs is not False:
            query = query.filter(or_(own_docs, lecteur_docs))
        else:
            query = query.filter(own_docs)

        if statut:
            query = query.filter_by(statut=statut)
        if categorie_id is not None:
            if str(categorie_id) in ('0', ''):
                query = query.filter(DocumentModel.categorie_id.is_(None))
            else:
                query = query.filter_by(categorie_id=int(categorie_id))
        query = Document._apply_search(query, search, ocr)

        total = query.count()
        page = max(1, page)
        limit = max(1, min(limit, 200))
        documents = (
            query.order_by(DocumentModel.date_creation.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return [doc.to_dict() for doc in documents], total

    @staticmethod
    def get_by_auteur_simple(auteur_id, entreprise_id=None):
        documents, _ = Document.get_by_auteur(auteur_id, limit=1000, entreprise_id=entreprise_id)
        return documents

    @staticmethod
    def get_by_entreprise(entreprise_id, search=None, statut=None, ocr=None, page=1, limit=100):
        query = (
            DocumentModel.query
            .filter_by(entreprise_id=entreprise_id)
            .filter(DocumentModel.supprime_le.is_(None))
            .filter(Document.ACTIVE_STATUSES_FILTER)
        )
        if statut:
            query = query.filter_by(statut=statut)
        query = Document._apply_search(query, search, ocr)

        total = query.count()
        page = max(1, page)
        limit = max(1, min(limit, 200))
        documents = (
            query.order_by(DocumentModel.date_creation.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return [doc.to_dict() for doc in documents], total

    @staticmethod
    def get_all(limit=100, search=None, statut=None, ocr=None, entreprise_id=None):
        query = DocumentModel.query.filter(
            DocumentModel.supprime_le.is_(None),
            Document.ACTIVE_STATUSES_FILTER,
        )
        if entreprise_id is not None:
            query = query.filter_by(entreprise_id=entreprise_id)
        if statut:
            query = query.filter_by(statut=statut)
        query = Document._apply_search(query, search, ocr)
        documents = query.order_by(DocumentModel.date_creation.desc()).limit(limit).all()
        return [doc.to_dict() for doc in documents]

    @staticmethod
    def get_all_paginated(limit=100, search=None, statut=None, ocr=None, entreprise_id=None, page=1):
        query = DocumentModel.query.filter(
            DocumentModel.supprime_le.is_(None),
            Document.ACTIVE_STATUSES_FILTER,
        )
        if entreprise_id is not None:
            query = query.filter_by(entreprise_id=entreprise_id)
        if statut:
            query = query.filter_by(statut=statut)
        query = Document._apply_search(query, search, ocr)
        total = query.count()
        page = max(1, page)
        limit = max(1, min(limit, 200))
        documents = (
            query.order_by(DocumentModel.date_creation.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return [doc.to_dict() for doc in documents], total

    @staticmethod
    def get_by_status(status, entreprise_id=None):
        query = DocumentModel.query.filter_by(statut=status).filter(
            DocumentModel.supprime_le.is_(None),
            Document.ACTIVE_STATUSES_FILTER,
        )
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
        document.date_modification = datetime.utcnow()

        if status == 'valide':
            document.validateur_id = validateur_id
            document.date_validation = datetime.utcnow()
        elif status == 'rejete':
            document.validateur_id = validateur_id
            document.commentaire_rejet = commentaire
        elif status == 'publie':
            document.validateur_id = validateur_id
            document.date_publication = datetime.utcnow()
            document.workflow_termine = True
        elif status == 'obsolete':
            document.date_obsolete = datetime.utcnow()
        elif status == 'detruit':
            document.date_detruit = datetime.utcnow()
        elif status == 'brouillon':
            document.commentaire_rejet = None

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
                'date_suppression': doc.supprime_le.isoformat() if doc.supprime_le else None,
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
            func.count().label('total'),
        )
        if entreprise_id is not None:
            query = query.filter(DocumentModel.entreprise_id == entreprise_id)
        query = query.filter(DocumentModel.date_creation >= func.date_sub(func.now(), func.interval(weeks, 'WEEK')))
        query = query.group_by(func.date_format(DocumentModel.date_creation, '%Y-%m-%d'))
        query = query.order_by('date_jour')
        results = query.all()
        return [{'date_jour': row.date_jour, 'total': row.total} for row in results]
