from extensions import db
from sqlalchemy import func
from models_sqlalchemy import Categorie, Document, Entreprise
import logging

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    ('Administratif', 'Documents administratifs et courriers'),
    ('Ressources humaines', 'Contrats, paie, dossiers RH'),
    ('Finance', 'Factures, budgets, comptabilité'),
    ('Juridique', 'Documents légaux et contrats'),
    ('Général', 'Documents divers'),
]


class CategoryService:
    """Service de gestion des catégories — une liste par entreprise."""

    @staticmethod
    def _base_query(entreprise_id=None):
        if entreprise_id is None:
            return Categorie.query.filter(Categorie.id == -1)
        return (
            Categorie.query.filter(Categorie.entreprise_id == entreprise_id)
            .order_by(Categorie.nom.asc())
        )

    @staticmethod
    def belongs_to_entreprise(categorie_id, entreprise_id):
        if categorie_id in (None, '', 0, '0'):
            return True
        if entreprise_id is None:
            return False
        cat = Categorie.query.get(int(categorie_id))
        return bool(cat and cat.entreprise_id == entreprise_id)

    @staticmethod
    def seed_default_categories(entreprise_id, commit=True):
        """Crée les catégories par défaut pour une nouvelle entreprise."""
        if not entreprise_id:
            return
        try:
            existing = {
                (c.nom or '').lower()
                for c in Categorie.query.filter_by(entreprise_id=entreprise_id).all()
            }
            added = False
            for nom, description in DEFAULT_CATEGORIES:
                if nom.lower() in existing:
                    continue
                db.session.add(Categorie(
                    nom=nom,
                    description=description,
                    entreprise_id=entreprise_id,
                ))
                added = True
            if added and commit:
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur seed_default_categories: {e}")
            raise

    @staticmethod
    def migrate_orphan_categories():
        """Rattache les catégories globales (entreprise_id NULL) à leur entreprise."""
        try:
            orphans = Categorie.query.filter(Categorie.entreprise_id.is_(None)).all()
            for cat in orphans:
                docs = Document.query.filter_by(categorie_id=cat.id).all()
                by_ent = {}
                for doc in docs:
                    if doc.entreprise_id:
                        by_ent.setdefault(doc.entreprise_id, []).append(doc)

                if len(by_ent) == 1:
                    cat.entreprise_id = next(iter(by_ent))
                elif len(by_ent) > 1:
                    first = True
                    for ent_id, doc_list in by_ent.items():
                        if first:
                            cat.entreprise_id = ent_id
                            first = False
                        else:
                            clone = Categorie(
                                nom=cat.nom,
                                description=cat.description,
                                entreprise_id=ent_id,
                            )
                            db.session.add(clone)
                            db.session.flush()
                            for doc in doc_list:
                                doc.categorie_id = clone.id
                else:
                    db.session.delete(cat)

            for company in Entreprise.query.all():
                count = Categorie.query.filter_by(entreprise_id=company.id).count()
                if count == 0:
                    CategoryService.seed_default_categories(company.id)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur migrate_orphan_categories: {e}")

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
            if entreprise_id is None:
                raise ValueError('Entreprise requise pour créer une catégorie')

            dup_query = Categorie.query.filter(
                Categorie.nom.ilike(nom),
                Categorie.entreprise_id == entreprise_id,
            )
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
            if entreprise_id is None:
                return False
            categorie = Categorie.query.filter_by(
                id=category_id, entreprise_id=entreprise_id
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
            if entreprise_id is None:
                return False
            categorie = Categorie.query.filter_by(
                id=category_id, entreprise_id=entreprise_id
            ).first()
            if not categorie:
                return False

            doc_count = Document.query.filter_by(
                categorie_id=category_id,
                entreprise_id=entreprise_id,
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
