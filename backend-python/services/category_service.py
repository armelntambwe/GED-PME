from extensions import db
from sqlalchemy import or_
from models_sqlalchemy import Categorie
import logging

logger = logging.getLogger(__name__)


class CategoryService:
    """Service de gestion des catégories via SQLAlchemy ORM."""

    @staticmethod
    def get_categories(entreprise_id=None):
        try:
            query = Categorie.query
            if entreprise_id is not None:
                query = query.filter(
                    or_(
                        Categorie.entreprise_id == entreprise_id,
                        Categorie.entreprise_id == None
                    )
                )
            categories = query.order_by(Categorie.nom.asc()).all()
            return [categorie.to_dict() for categorie in categories]
        except Exception as e:
            logger.error(f"Erreur get_categories: {e}")
            raise

    @staticmethod
    def create_category(nom, description, entreprise_id=None):
        try:
            categorie = Categorie(
                nom=nom,
                description=description,
                entreprise_id=entreprise_id
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
            categorie = Categorie.query.filter(
                Categorie.id == category_id,
                or_(
                    Categorie.entreprise_id == entreprise_id,
                    Categorie.entreprise_id == None
                )
            ).first()
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
            categorie = Categorie.query.filter(
                Categorie.id == category_id,
                or_(
                    Categorie.entreprise_id == entreprise_id,
                    Categorie.entreprise_id == None
                )
            ).first()
            if not categorie:
                return False
            db.session.delete(categorie)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur delete_category: {e}")
            raise