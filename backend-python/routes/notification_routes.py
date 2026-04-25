from flask import request, jsonify
from middleware.auth import token_required
from utils.db import get_db
from datetime import datetime

def register_notification_routes(app):

    @app.route("/notifications/all", methods=["GET"])
    @token_required
    def get_all_notifications():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, type, message, lien, lue, date_creation
                FROM notifications
                WHERE user_id = %s
                ORDER BY date_creation DESC
                LIMIT 50
            """, (request.user_id,))
            notifications = cur.fetchall()
            cur.close()
            conn.close()
            
            for n in notifications:
                if n.get('date_creation'):
                    n['date_creation'] = str(n['date_creation'])
            
            return jsonify({"success": True, "notifications": notifications}), 200
        except Exception as e:
            print(f"[ERREUR] get_all_notifications: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/notifications/<int:notif_id>/lire", methods=["PUT"])
    @token_required
    def marquer_notification_lue(notif_id):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE notifications SET lue = 1
                WHERE id = %s AND user_id = %s
            """, (notif_id, request.user_id))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"success": True, "message": "Notification marquée comme lue"}), 200
        except Exception as e:
            print(f"[ERREUR] marquer_notification_lue: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/notifications/lire-tout", methods=["PUT"])
    @token_required
    def marquer_tout_lu():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE notifications SET lue = 1
                WHERE user_id = %s
            """, (request.user_id,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"success": True, "message": "Toutes les notifications ont été marquées comme lues"}), 200
        except Exception as e:
            print(f"[ERREUR] marquer_tout_lu: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/notifications/count", methods=["GET"])
    @token_required
    def get_notifications_count():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) as total FROM notifications
                WHERE user_id = %s AND lue = 0
            """, (request.user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            return jsonify({"success": True, "count": result['total'] or 0}), 200
        except Exception as e:
            print(f"[ERREUR] get_notifications_count: {e}")
            return jsonify({"success": False, "message": str(e)}), 500