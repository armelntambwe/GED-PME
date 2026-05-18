from extensions import db
from sqlalchemy import or_
from models_sqlalchemy import Categorie as CategorieModel

class Categorie:
    """Classe modèle pour les catégories"""

    @staticmethod
    def create(nom, description=None, entreprise_id=None):
        categorie = CategorieModel(
            nom=nom,
            description=description,
            entreprise_id=entreprise_id
        )
        db.session.add(categorie)
        db.session.commit()
        return categorie.id

    @staticmethod
    def get_all():
        categories = CategorieModel.query.order_by(CategorieModel.nom.asc()).all()
        return [categorie.to_dict() for categorie in categories]

    @staticmethod
    def get_accessible_by_entreprise(entreprise_id):
        categories = (
            CategorieModel.query
            .filter(or_(CategorieModel.entreprise_id == entreprise_id, CategorieModel.entreprise_id.is_(None)))
            .order_by(CategorieModel.nom.asc())
            .all()
        )
        return [categorie.to_dict() for categorie in categories]

    @staticmethod
    def get_by_id(categorie_id):
        categorie = CategorieModel.query.get(categorie_id)
        return categorie.to_dict() if categorie else None

    @staticmethod
    def update(categorie_id, nom=None, description=None):
        categorie = CategorieModel.query.get(categorie_id)
        if not categorie:
            return False
        if nom is not None:
            categorie.nom = nom
        if description is not None:
            categorie.description = description
        db.session.commit()
        return True

    @staticmethod
    def delete(categorie_id):
        categorie = CategorieModel.query.get(categorie_id)
        if not categorie:
            return False
        db.session.delete(categorie)
        db.session.commit()
        return True
