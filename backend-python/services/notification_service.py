# services/notification_service.py
# Service de notifications - Logique métier des notifications

from models.notification import Notification
from models.log import Log

class NotificationService:
    """Service de gestion des notifications"""

    @staticmethod
    def send_to_user(user_id, type_notif, message, lien=None):
        """
        Envoie une notification à un utilisateur spécifique
        Retourne: (success, notification_id)
        """
        notif_id = Notification.create(user_id, type_notif, message, lien)
        return True, notif_id

    @staticmethod
    def send_to_admins(entreprise_id, type_notif, message, lien=None):
        """
        Envoie une notification à tous les administrateurs d'une entreprise
        Retourne: (success, count)
        """
        result = Notification.send_to_admins(entreprise_id, type_notif, message, lien)
        return True, result

    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=50):
        """
        Récupère les notifications d'un utilisateur
        Retourne: (success, notifications)
        """
        if unread_only:
            notifs = Notification.get_unread(user_id, limit)
        else:
            notifs = Notification.get_all(user_id, limit)

        return True, notifs

    @staticmethod
    def mark_as_read(notif_id, user_id):
        """
        Marque une notification comme lue
        Retourne: (success, message)
        """
        Notification.mark_as_read(notif_id, user_id)
        return True, "Notification marquée comme lue"

    @staticmethod
    def mark_all_as_read(user_id):
        """
        Marque toutes les notifications comme lues
        Retourne: (success, message)
        """
        Notification.mark_all_as_read(user_id)
        return True, "Toutes les notifications ont été marquées comme lues"

    @staticmethod
    def count_unread(user_id):
        """
        Compte les notifications non lues d'un utilisateur
        Retourne: (success, count)
        """
        count = Notification.count_unread(user_id)
        return True, count