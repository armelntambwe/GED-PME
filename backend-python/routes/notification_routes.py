# routes/notification_routes.py
from flask import request, jsonify
from middleware.auth import token_required
from models.notification import Notification

def register_notification_routes(app):

    @app.route("/notifications", methods=["GET"])
    @token_required
    def get_notifications():
        notifs = Notification.get_unread(request.user_id)
        for n in notifs:
            if n.get('date_creation'):
                n['date_creation'] = str(n['date_creation'])
        return jsonify({"success": True, "notifications": notifs}), 200

    @app.route("/notifications/all", methods=["GET"])
    @token_required
    def get_all_notifications():
        notifs = Notification.get_all(request.user_id)
        for n in notifs:
            if n.get('date_creation'):
                n['date_creation'] = str(n['date_creation'])
        return jsonify({"success": True, "notifications": notifs}), 200

    @app.route("/notifications/<int:notif_id>/lire", methods=["PUT"])
    @token_required
    def lire_notification(notif_id):
        Notification.mark_as_read(notif_id, request.user_id)
        return jsonify({"success": True}), 200

    @app.route("/notifications/lire-tout", methods=["PUT"])
    @token_required
    def lire_toutes_notifications():
        Notification.mark_all_as_read(request.user_id)
        return jsonify({"success": True}), 200

    @app.route("/notifications/count", methods=["GET"])
    @token_required
    def count_notifications():
        count = Notification.count_unread(request.user_id)
        return jsonify({"success": True, "count": count}), 200