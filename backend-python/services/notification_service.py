# services/notification_service.py
# Service de notifications - Logique métier des notifications

from extensions import db
from models_sqlalchemy import Notification
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service de gestion des notifications utilisant ORM SQLAlchemy."""
    
    @staticmethod
    def get_user_notifications(user_id: int, limit: int = 50) -> list:
        """Récupère toutes les notifications d'un utilisateur."""
        try:
            notifications = Notification.query.filter_by(user_id=user_id)\
                .order_by(Notification.date_creation.desc())\
                .limit(limit)\
                .all()
            
            return [notif.to_dict() for notif in notifications]
        except Exception as e:
            logger.error(f"Erreur get_user_notifications: {e}")
            raise
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Marque une notification comme lue."""
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                notification.lue = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur mark_as_read: {e}")
            raise
    
    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Marque toutes les notifications d'un utilisateur comme lues. Retourne le nombre de notifications marquées."""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                lue=False
            ).update({'lue': True})
            
            db.session.commit()
            return count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur mark_all_as_read: {e}")
            raise
    
    @staticmethod
    def count_unread(user_id: int) -> int:
        """Compte les notifications non lues d'un utilisateur."""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                lue=False
            ).count()
            
            return count
        except Exception as e:
            logger.error(f"Erreur count_unread: {e}")
            raise
    
    @staticmethod
    def create_notification(user_id: int, type_notif: str, message: str, lien: str = None) -> int:
        """Crée une nouvelle notification. Retourne l'ID de la notification créée."""
        try:
            notification = Notification(
                user_id=user_id,
                type_notif=type_notif,
                message=message,
                lien=lien,
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            return notification.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_notification: {e}")
            raise