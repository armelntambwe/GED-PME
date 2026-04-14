# routes/admin_routes.py
from flask import request, jsonify, send_file
from middleware.auth import token_required, role_required
from services.admin_service import AdminService
from services.document_service import DocumentService
from models.document import Document
from models.log import Log
from models.notification import Notification
from config import Config, UPLOAD_FOLDER
from utils.db import get_db
import os
import csv
from io import StringIO
from datetime import datetime
import subprocess
import shutil

def register_admin_routes(app):

    @app.route("/api/admin-global/stats", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_stats():
        stats = AdminService.get_global_stats()
        return jsonify({"success": True, "stats": stats}), 200

    @app.route("/api/admin-global/entreprises", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def get_all_entreprises():
        entreprises = AdminService.get_all_entreprises()
        return jsonify({"success": True, "entreprises": entreprises}), 200

    @app.route("/api/admin-global/entreprises", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def create_entreprise():
        data = request.json
        if not data or not data.get('nom'):
            return jsonify({"success": False, "message": "Nom requis"}), 400
        
        success, message, entreprise_id = AdminService.create_entreprise(
            data['nom'], data.get('adresse', ''), data.get('telephone', ''), data.get('email', '')
        )
        
        if success:
            Notification.create(
                user_id=request.user_id,
                type_notif='ENTREPRISE_CREEE',
                message=f"L'entreprise {data['nom']} a été créée",
                lien='/dashboard-admin-global?tab=entreprises'
            )
        
        return jsonify({"success": success, "message": message, "entreprise_id": entreprise_id}), 201 if success else 400

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def update_entreprise(entreprise_id):
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT nom FROM entreprises WHERE id = %s", (entreprise_id,))
        ent = cur.fetchone()
        if not ent:
            return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
        
        success, message = AdminService.update_entreprise(
            entreprise_id, data.get('nom'), data.get('adresse'), data.get('telephone'), data.get('email')
        )
        
        if success:
            Notification.create(
                user_id=request.user_id,
                type_notif='ENTREPRISE_MODIFIEE',
                message=f"L'entreprise {data.get('nom', ent['nom'])} a été modifiée",
                lien='/dashboard-admin-global?tab=entreprises'
            )
        
        return jsonify({"success": success, "message": message}), 200 if success else 400

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def toggle_entreprise(entreprise_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT nom, statut FROM entreprises WHERE id = %s", (entreprise_id,))
        ent = cur.fetchone()
        if not ent:
            return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
        
        nouvel_etat = 'suspendu' if ent['statut'] == 'actif' else 'actif'
        success, message = AdminService.toggle_entreprise(entreprise_id)
        
        if success:
            Notification.create(
                user_id=request.user_id,
                type_notif='ENTREPRISE_TOGGLE',
                message=f"L'entreprise {ent['nom']} est maintenant {nouvel_etat}",
                lien='/dashboard-admin-global?tab=entreprises'
            )
        
        return jsonify({"success": success, "message": message}), 200 if success else 404

    @app.route("/api/admin-global/all-users", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def get_all_users():
        users = AdminService.get_all_users()
        return jsonify({"success": True, "users": users}), 200

    @app.route("/api/admin-global/all-documents", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def get_all_documents():
        limit = request.args.get('limit', 100, type=int)
        documents = AdminService.get_all_documents(limit)
        return jsonify({"success": True, "documents": documents}), 200

    @app.route("/api/admin-global/all-logs", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def get_all_logs():
        limit = request.args.get('limit', 200, type=int)
        logs = AdminService.get_all_logs(limit)
        return jsonify({"success": True, "logs": logs}), 200

    @app.route("/api/admin-global/stats/evolution", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def stats_evolution():
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT DATE_FORMAT(date_creation, '%Y-%m-%d') as date_jour, COUNT(*) as total
                FROM documents
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL 8 WEEK) AND supprime_le IS NULL
                GROUP BY DATE(date_creation)
                ORDER BY date_jour ASC
            """)
            results = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({
                "success": True,
                "labels": [r['date_jour'] for r in results],
                "data": [r['total'] for r in results]
            }), 200
        except Exception as e:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/storage", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def get_storage_info():
        storage = AdminService.get_storage_info()
        return jsonify({"success": True, "storage": storage}), 200

    @app.route("/api/admin-global/logs/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def export_logs_csv():
        logs = Log.get_all(limit=1000)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Action', 'Description', 'Utilisateur', 'Entreprise'])
        for log in logs:
            writer.writerow([
                log.get('date_action', ''),
                log.get('action', ''),
                log.get('description', ''),
                log.get('utilisateur_nom', ''),
                log.get('entreprise_nom', '')
            ])
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mimetype='text/csv'
        )

    @app.route("/api/admin-global/backup", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def manual_backup():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"backups/backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        try:
            subprocess.run([
                'mysqldump', '-u', Config.MYSQL_USER,
                f'-p{Config.MYSQL_PASSWORD}', Config.MYSQL_DB,
                '--result-file', f"{backup_dir}/database.sql"
            ], check=True)
            shutil.copytree(UPLOAD_FOLDER, f"{backup_dir}/uploads")
            
            Notification.create(
                user_id=request.user_id,
                type_notif='BACKUP_EFFECTUE',
                message=f"Sauvegarde manuelle effectuée à {timestamp}",
                lien='/dashboard-admin-global?tab=storage'
            )
            
            return jsonify({"success": True, "backup_path": backup_dir}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500