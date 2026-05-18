from extensions import db
from models_sqlalchemy import Log as LogModel, User as UserModel

class Log:
    """Classe modèle pour les logs"""

    @staticmethod
    def create(action, description, user_id, document_id=None, ip_adresse=None):
        log = LogModel(
            action=action,
            description=description,
            user_id=user_id,
            document_id=document_id,
            adresse_ip=ip_adresse
        )
        db.session.add(log)
        db.session.commit()
        return log.id

    @staticmethod
    def get_all(limit=200):
        logs = (
            LogModel.query
            .order_by(LogModel.date_action.desc())
            .limit(limit)
            .all()
        )
        return [log.to_dict() for log in logs]

    @staticmethod
    def get_by_user(user_id, limit=50):
        logs = (
            LogModel.query
            .filter_by(user_id=user_id)
            .order_by(LogModel.date_action.desc())
            .limit(limit)
            .all()
        )
        return [log.to_dict() for log in logs]

    @staticmethod
    def get_by_document(document_id, limit=50):
        logs = (
            LogModel.query
            .filter_by(document_id=document_id)
            .order_by(LogModel.date_action.desc())
            .limit(limit)
            .all()
        )
        return [log.to_dict() for log in logs]

    @staticmethod
    def get_by_entreprise(entreprise_id, limit=50):
        logs = (
            db.session.query(LogModel)
            .join(LogModel.user)
            .filter(LogModel.user.has(entreprise_id=entreprise_id))
            .order_by(LogModel.date_action.desc())
            .limit(limit)
            .all()
        )
        return [log.to_dict() for log in logs]

    @staticmethod
    def filter_logs(date_debut=None, date_fin=None, action=None, limit=500):
        query = LogModel.query
        if date_debut:
            query = query.filter(LogModel.date_action >= date_debut)
        if date_fin:
            query = query.filter(LogModel.date_action <= date_fin)
        if action:
            query = query.filter_by(action=action)
        logs = query.order_by(LogModel.date_action.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]
