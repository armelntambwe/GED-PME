from extensions import db
from models_sqlalchemy import User as UserModel

class User:

    @staticmethod
    def find_by_email(email):
        return UserModel.query.filter_by(email=email).first()

    @staticmethod
    def find_by_id(user_id):
        return UserModel.query.get(user_id)

    @staticmethod
    def create(nom, email, password_hash, role, telephone=None, entreprise_id=None):
        user = UserModel(
            nom=nom,
            email=email,
            password=password_hash,
            telephone=telephone,
            role=role,
            entreprise_id=entreprise_id,
            actif=True
        )
        db.session.add(user)
        db.session.commit()
        return user.id

    @staticmethod
    def get_all():
        users = UserModel.query.order_by(UserModel.id.desc()).all()
        return [user.to_dict() for user in users]

    @staticmethod
    def get_employees(entreprise_id=None):
        query = UserModel.query.filter_by(role='employe')
        if entreprise_id is not None:
            query = query.filter_by(entreprise_id=entreprise_id)
        users = query.order_by(UserModel.id.desc()).all()
        return [user.to_dict() for user in users]

    @staticmethod
    def deactivate(user_id):
        user = UserModel.query.get(user_id)
        if not user:
            return False
        user.actif = False
        db.session.commit()
        return True

    @staticmethod
    def set_active(user_id, active=True):
        user = UserModel.query.get(user_id)
        if not user:
            return False
        user.actif = bool(active)
        db.session.commit()
        return True

    @staticmethod
    def toggle_active(user_id):
        user = UserModel.query.get(user_id)
        if not user:
            return None
        user.actif = not user.actif
        db.session.commit()
        return user.actif

    @staticmethod
    def update_profile(user_id, nom=None, telephone=None, password_hash=None):
        user = UserModel.query.get(user_id)
        if not user:
            return False
        if nom is not None:
            user.nom = nom
        if telephone is not None:
            user.telephone = telephone
        if password_hash is not None:
            user.password = password_hash
        db.session.commit()
        return True

    @staticmethod
    def reset_password(user_id, password_hash):
        user = UserModel.query.get(user_id)
        if not user:
            return False
        user.password = password_hash
        db.session.commit()
        return True