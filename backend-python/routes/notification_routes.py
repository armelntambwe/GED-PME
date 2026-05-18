from flask import request, jsonify
from middleware.auth import token_required
from services.notification_service import NotificationService

def register_notification_routes(app):

    @app.route("/notifications/all", methods=["GET"])
    @token_required
    def get_all_notifications():
        try:
            notifications = NotificationService.get_user_notifications(request.user_id)
            
            return jsonify({"success": True, "notifications": notifications}), 200
        except Exception as e:
            print(f"[ERREUR] get_all_notifications: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/notifications/<int:notif_id>/lire", methods=["PUT"])
    @token_required
    def marquer_notification_lue(notif_id):
        try:
            success = NotificationService.mark_as_read(notif_id, request.user_id)
            if success:
                return jsonify({"success": True, "message": "Notification marquée comme lue"}), 200
            else:
                return jsonify({"success": False, "message": "Notification non trouvée"}), 404
        except Exception as e:
            print(f"[ERREUR] marquer_notification_lue: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/notifications/lire-tout", methods=["PUT"])
    @token_required
    def marquer_tout_lu():
        try:
            count = NotificationService.mark_all_as_read(request.user_id)
            return jsonify({"success": True, "message": f"{count} notifications marquées comme lues"}), 200
        except Exception as e:
            print(f"[ERREUR] marquer_tout_lu: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/notifications/count", methods=["GET"])
    @token_required
    def get_notifications_count():
        try:
            count = NotificationService.count_unread(request.user_id)
            return jsonify({"success": True, "count": count}), 200
        except Exception as e:
            print(f"[ERREUR] get_notifications_count: {e}")
            return jsonify({"success": False, "message": str(e)}), 500