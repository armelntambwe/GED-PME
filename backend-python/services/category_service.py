from extensions import db
from sqlalchemy import func
from models_sqlalchemy import Categorie, Document
import logging

logger = logging.getLogger(__name__)


class CategoryService:
    """Service de gestion des catégories."""

    @staticmethod
    def _base_query(entreprise_id=None):
        query = Categorie.query
        if entreprise_id is not None:
            query = query.filter(Categorie.entreprise_id == entreprise_id)
        return query.order_by(Categorie.nom.asc())

    @staticmethod
    def get_categories(entreprise_id=None):
        try:
            categories = CategoryService._base_query(entreprise_id).all()
            counts = {}
            if entreprise_id is not None:
                rows = (
                    db.session.query(Document.categorie_id, func.count(Document.id))
                    .filter(
                        Document.entreprise_id == entreprise_id,
                        Document.supprime_le.is_(None),
                    )
                    .group_by(Document.categorie_id)
                    .all()
                )
                counts = {cid: n for cid, n in rows if cid}
            result = []
            for categorie in categories:
                data = categorie.to_dict()
                data['nb_documents'] = counts.get(categorie.id, 0)
                result.append(data)
            return result
        except Exception as e:
            logger.error(f"Erreur get_categories: {e}")
            raise

    @staticmethod
    def create_category(nom, description, entreprise_id=None):
        try:
            nom = (nom or '').strip()
            if not nom:
                raise ValueError('Le nom de la catégorie est requis')

            dup_query = Categorie.query.filter(Categorie.nom.ilike(nom))
            if entreprise_id is not None:
                dup_query = dup_query.filter(Categorie.entreprise_id == entreprise_id)
            if dup_query.first():
                raise ValueError(f'La catégorie « {nom} » existe déjà')

            categorie = Categorie(
                nom=nom,
                description=description,
                entreprise_id=entreprise_id,
            )
            db.session.add(categorie)
            db.session.commit()
            return categorie.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_category: {e}")
            raise

    @staticmethod
    def update_category(category_id, nom, description, entreprise_id=None):
        try:
            query = Categorie.query.filter_by(id=category_id)
            if entreprise_id is not None:
                query = query.filter(Categorie.entreprise_id == entreprise_id)
            categorie = query.first()
            if not categorie:
                return False
            categorie.nom = nom
            categorie.description = description
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_category: {e}")
            raise

    @staticmethod
    def delete_category(category_id, entreprise_id=None):
        try:
            query = Categorie.query.filter_by(id=category_id)
            if entreprise_id is not None:
                query = query.filter(Categorie.entreprise_id == entreprise_id)
            categorie = query.first()
            if not categorie:
                return False

            doc_count = Document.query.filter_by(
                categorie_id=category_id
            ).filter(Document.supprime_le.is_(None)).count()
            if doc_count > 0:
                raise ValueError(
                    f"Impossible de supprimer : {doc_count} document(s) utilisent cette catégorie"
                )

            db.session.delete(categorie)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur delete_category: {e}")
            raise
