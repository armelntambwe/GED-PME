from extensions import db
from models_sqlalchemy import Entreprise as EntrepriseModel, User as UserModel, Document as DocumentModel

class Entreprise:
    """Classe modèle pour les entreprises"""

    @staticmethod
    def create(nom, adresse=None, telephone=None, email=None):
        entreprise = EntrepriseModel(
            nom=nom,
            adresse=adresse,
            telephone=telephone,
            email=email
        )
        db.session.add(entreprise)
        db.session.commit()
        return entreprise.id

    @staticmethod
    def get_all():
        entreprises = EntrepriseModel.query.order_by(EntrepriseModel.nom.asc()).all()
        result = []
        for entreprise in entreprises:
            nb_employes = UserModel.query.filter_by(entreprise_id=entreprise.id).count()
            nb_documents = DocumentModel.query.filter_by(entreprise_id=entreprise.id).count()
            data = entreprise.to_dict()
            data['nb_employes'] = nb_employes
            data['nb_documents'] = nb_documents
            result.append(data)
        return result

    @staticmethod
    def get_by_id(entreprise_id):
        entreprise = EntrepriseModel.query.get(entreprise_id)
        return entreprise.to_dict() if entreprise else None

    @staticmethod
    def update(entreprise_id, nom=None, adresse=None, telephone=None, email=None):
        entreprise = EntrepriseModel.query.get(entreprise_id)
        if not entreprise:
            return False
        if nom is not None:
            entreprise.nom = nom
        if adresse is not None:
            entreprise.adresse = adresse
        if telephone is not None:
            entreprise.telephone = telephone
        if email is not None:
            entreprise.email = email
        db.session.commit()
        return True

    @staticmethod
    def toggle_status(entreprise_id):
        entreprise = EntrepriseModel.query.get(entreprise_id)
        if not entreprise:
            return None
        nouvel_etat = 'suspendu' if entreprise.statut == 'actif' else 'actif'
        entreprise.statut = nouvel_etat
        db.session.commit()
        return nouvel_etat

    @staticmethod
    def set_status(entreprise_id, statut):
        entreprise = EntrepriseModel.query.get(entreprise_id)
        if not entreprise:
            return False
        entreprise.statut = statut
        db.session.commit()
        return True

    @staticmethod
    def get_stats(entreprise_id):
        total_documents = DocumentModel.query.filter_by(entreprise_id=entreprise_id).count()
        total_employes = UserModel.query.filter_by(entreprise_id=entreprise_id, role='employe').count()
        en_attente = DocumentModel.query.filter_by(entreprise_id=entreprise_id, statut='soumis').count()
        valides = DocumentModel.query.filter_by(entreprise_id=entreprise_id, statut='valide').count()
        return {
            'total_documents': total_documents,
            'total_employes': total_employes,
            'en_attente': en_attente,
            'valides': valides
        }
