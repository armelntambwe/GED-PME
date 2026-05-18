from extensions import db
from models_sqlalchemy import Notification as NotificationModel, User as UserModel

class Notification:
    """Classe modèle pour les notifications"""

    @staticmethod
    def create(user_id, type_notif, message, lien=None):
        notif = NotificationModel(
            user_id=user_id,
            type_notif=type_notif,
            message=message,
            lien=lien,
            lue=False
        )
        db.session.add(notif)
        db.session.commit()
        return notif.id

    @staticmethod
    def get_unread(user_id, limit=50):
        notifs = (
            NotificationModel.query
            .filter_by(user_id=user_id, lue=False)
            .order_by(NotificationModel.date_creation.desc())
            .limit(limit)
            .all()
        )
        return [notif.to_dict() for notif in notifs]

    @staticmethod
    def get_all(user_id, limit=100):
        notifs = (
            NotificationModel.query
            .filter_by(user_id=user_id)
            .order_by(NotificationModel.date_creation.desc())
            .limit(limit)
            .all()
        )
        return [notif.to_dict() for notif in notifs]

    @staticmethod
    def mark_as_read(notif_id, user_id):
        notif = NotificationModel.query.filter_by(id=notif_id, user_id=user_id).first()
        if not notif:
            return False
        notif.lue = True
        db.session.commit()
        return True

    @staticmethod
    def mark_all_as_read(user_id):
        NotificationModel.query.filter_by(user_id=user_id, lue=False).update(
            {'lue': True}, synchronize_session='fetch'
        )
        db.session.commit()
        return True

    @staticmethod
    def count_unread(user_id):
        return NotificationModel.query.filter_by(user_id=user_id, lue=False).count()

    @staticmethod
    def send_to_admins(entreprise_id, type_notif, message, lien=None):
        admins = UserModel.query.filter_by(
            entreprise_id=entreprise_id,
            role='admin_pme'
        ).all()
        for admin in admins:
            Notification.create(admin.id, type_notif, message, lien)
        return True
