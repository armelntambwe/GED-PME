# routes/admin_routes.py
from flask import request, jsonify, send_file
from middleware.auth import token_required, role_required
from services.user_service import UserService
from services.admin_service_orm import AdminService
from models_sqlalchemy import Entreprise, User, Document, Log, Notification
from extensions import db
from werkzeug.security import generate_password_hash
from config import Config
import csv
from datetime import datetime, timedelta
from io import BytesIO
import os
import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)


def register_admin_routes(app):

    # ============================================
    # STATISTIQUES
    # ============================================

    @app.route("/api/admin-global/stats", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_stats():
        try:
            stats = AdminService.get_global_stats()
            return jsonify({"success": True, "stats": stats}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_stats: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # GESTION UTILISATEURS
    # ============================================

    @app.route("/api/admin-global/users/<int:user_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_toggle_user(user_id):
        try:
            result = AdminService.toggle_user(user_id)
            if result is None:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            return jsonify({"success": True, "message": result['message'], "user": result}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_toggle_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/<int:user_id>/reset-password", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_reset_password(user_id):
        try:
            data = request.json or {}
            new_password = data.get('password', 'employe123')
            if len(new_password) < 6:
                return jsonify({"success": False, "message": "Le mot de passe doit contenir au moins 6 caractères"}), 400

            user = UserService.get_user_by_id(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            password_hash = generate_password_hash(new_password)
            UserService.update_user_password(user_id, password_hash)

            notification = Notification(
                user_id=request.user_id,
                type_notif='PASSWORD_RESET',
                message=f"Le mot de passe de l'utilisateur {user['nom']} a été réinitialisé",
                lien='/dashboard-admin-global?tab=users',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": f"Mot de passe réinitialisé à {new_password}"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_reset_password: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # ENTREPRISES
    # ============================================

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/delete", methods=["DELETE"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_delete_entreprise(entreprise_id):
        try:
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

            entreprise.statut = 'suspendu'
            notification = Notification(
                user_id=request.user_id,
                type_notif='ENTREPRISE_SUPPRIMEE',
                message=f"L'entreprise {entreprise.nom} a été supprimée (soft delete)",
                lien='/dashboard-admin-global?tab=entreprises',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Entreprise supprimée (soft delete)"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_delete_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_export_entreprises():
        try:
            entreprises = Entreprise.query.order_by(Entreprise.id.desc()).all()
            from io import StringIO
            output = StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(['ID', 'Nom', 'Email', 'Telephone', 'Adresse', 'Statut', 'Date creation', 'Employes', 'Documents'])
            for e in entreprises:
                nb_employes = User.query.filter_by(entreprise_id=e.id, role='employe').count()
                nb_documents = Document.query.filter_by(entreprise_id=e.id).count()
                writer.writerow([
                    str(e.id),
                    e.nom,
                    e.email or '',
                    e.telephone or '',
                    e.adresse or '',
                    e.statut,
                    e.date_creation.isoformat() if e.date_creation else '',
                    str(nb_employes),
                    str(nb_documents)
                ])
            # Convert text to bytes for send_file
            bytes_out = BytesIO(output.getvalue().encode('utf-8'))
            bytes_out.seek(0)
            return send_file(bytes_out, as_attachment=True, download_name=f"entreprises_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv", mimetype='text/csv')
        except Exception as e:
            logger.error(f"Erreur admin_global_export_entreprises: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_export_users():
        try:
            users = User.query.order_by(User.id.desc()).all()
            from io import StringIO
            output = StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(['ID', 'Nom', 'Email', 'Telephone', 'Role', 'Actif', 'Date inscription', 'Entreprise'])
            for u in users:
                entreprise = Entreprise.query.get(u.entreprise_id) if u.entreprise_id else None
                writer.writerow([
                    str(u.id),
                    u.nom,
                    u.email or '',
                    u.telephone or '',
                    u.role or '',
                    'Actif' if u.actif else 'Inactif',
                    u.date_inscription.isoformat() if u.date_inscription else '',
                    entreprise.nom if entreprise else ''
                ])
            bytes_out = BytesIO(output.getvalue().encode('utf-8'))
            bytes_out.seek(0)
            return send_file(bytes_out, as_attachment=True, download_name=f"utilisateurs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv", mimetype='text/csv')
        except Exception as e:
            logger.error(f"Erreur admin_global_export_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/logs/filter", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_filter_logs():
        try:
            date_debut = request.args.get('date_debut')
            date_fin = request.args.get('date_fin')
            action = request.args.get('action')

            query = Log.query
            if date_debut:
                query = query.filter(Log.date_action >= datetime.fromisoformat(date_debut))
            if date_fin:
                query = query.filter(Log.date_action <= datetime.fromisoformat(date_fin))
            if action:
                query = query.filter_by(action=action)

            logs = query.order_by(Log.date_action.desc()).limit(500).all()
            return jsonify({"success": True, "logs": [log.to_dict() for log in logs]}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_filter_logs: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # ENTREPRISES (CRUD)
    # ============================================

    @app.route("/api/admin-global/entreprises", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_entreprises():
        try:
            entreprises = Entreprise.query.order_by(Entreprise.id.desc()).all()
            result = []
            for e in entreprises:
                result.append({
                    **e.to_dict(),
                    'nb_employes': User.query.filter_by(entreprise_id=e.id, role='employe').count(),
                    'nb_documents': Document.query.filter_by(entreprise_id=e.id).count()
                })
            return jsonify({"success": True, "entreprises": result}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_entreprises: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_create_entreprise():
        try:
            data = request.json or {}
            nom = data.get('nom')
            if not nom:
                return jsonify({"success": False, "message": "Nom requis"}), 400

            entreprise = Entreprise(
                nom=nom,
                email=data.get('email'),
                telephone=data.get('telephone'),
                adresse=data.get('adresse'),
                statut='actif'
            )
            db.session.add(entreprise)
            db.session.commit()

            notification = Notification(
                user_id=request.user_id,
                type_notif='ENTREPRISE_CREEE',
                message=f"L'entreprise {entreprise.nom} a été créée",
                lien='/dashboard-admin-global?tab=entreprises',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Entreprise créée", "entreprise_id": entreprise.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_create_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_update_entreprise(entreprise_id):
        try:
            data = request.json or {}
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

            old_nom = entreprise.nom
            entreprise.nom = data.get('nom', entreprise.nom)
            entreprise.email = data.get('email', entreprise.email)
            entreprise.telephone = data.get('telephone', entreprise.telephone)
            entreprise.adresse = data.get('adresse', entreprise.adresse)
            db.session.commit()

            notification = Notification(
                user_id=request.user_id,
                type_notif='ENTREPRISE_MODIFIEE',
                message=f"L'entreprise {old_nom} a été modifiée",
                lien='/dashboard-admin-global?tab=entreprises',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Entreprise modifiée"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_update_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_toggle_entreprise(entreprise_id):
        try:
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

            entreprise.statut = 'suspendu' if entreprise.statut == 'actif' else 'actif'
            db.session.commit()

            notification = Notification(
                user_id=request.user_id,
                type_notif='ENTREPRISE_TOGGLE',
                message=f"L'entreprise {entreprise.nom} est maintenant {entreprise.statut}",
                lien='/dashboard-admin-global?tab=entreprises',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": f"Statut changé en {entreprise.statut}"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_toggle_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # UTILISATEURS
    # ============================================

    @app.route("/api/admin-global/all-users", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_users():
        try:
            users = User.query.order_by(User.id.desc()).all()
            result = []
            for u in users:
                entreprise = Entreprise.query.get(u.entreprise_id) if u.entreprise_id else None
                result.append({
                    'id': u.id,
                    'nom': u.nom,
                    'email': u.email,
                    'role': u.role,
                    'actif': u.actif,
                    'entreprise_nom': entreprise.nom if entreprise else None
                })
            return jsonify({"success": True, "users": result}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # DOCUMENTS
    # ============================================

    @app.route("/api/admin-global/all-documents", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_documents():
        try:
            documents = Document.query.filter(
                (Document.supprime_le == None) | (Document.supprime_le == '')
            ).order_by(Document.date_creation.desc()).limit(100).all()
            return jsonify({"success": True, "documents": [doc.to_dict() for doc in documents]}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_documents: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # LOGS
    # ============================================

    @app.route("/api/admin-global/all-logs", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_logs():
        try:
            logs = Log.query.order_by(Log.date_action.desc()).limit(200).all()
            return jsonify({"success": True, "logs": [log.to_dict() for log in logs]}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_logs: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/logs/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_logs_export():
        try:
            logs = Log.query.order_by(Log.date_action.desc()).limit(1000).all()
            from io import StringIO
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Date', 'Action', 'Description', 'Utilisateur'])
            for log in logs:
                writer.writerow([
                    log.date_action.isoformat() if log.date_action else '',
                    log.action,
                    log.description or '',
                    log.user.nom if log.user else ''
                ])
            bytes_out = BytesIO(output.getvalue().encode('utf-8'))
            bytes_out.seek(0)
            return send_file(bytes_out, as_attachment=True, download_name=f"logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv", mimetype='text/csv')
        except Exception as e:
            logger.error(f"Erreur admin_global_logs_export: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # STOCKAGE
    # ============================================

    @app.route("/api/admin-global/storage", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_storage():
        try:
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            total_size = 0
            if os.path.exists(upload_folder):
                for dirpath, dirnames, filenames in os.walk(upload_folder):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
            used_mb = total_size // (1024 * 1024)
            total_mb = 1024
            used_gb = round(used_mb / 1024, 2)
            total_gb = 1
            free_gb = round(total_gb - used_gb, 2)
            percent = round((used_mb / total_mb) * 100, 1) if total_mb else 0
            return jsonify({"success": True, "storage": {"used_mb": used_mb, "total_mb": total_mb, "used_gb": used_gb, "total_gb": total_gb, "free_gb": free_gb, "uploads_mb": used_mb, "percent": percent}}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_storage: {e}")
            return jsonify({"success": True, "storage": {"used_mb": 0, "total_mb": 1024, "used_gb": 0, "total_gb": 1, "free_gb": 1, "uploads_mb": 0, "percent": 0}}), 200

    # ============================================
    # BACKUP
    # ============================================

    @app.route("/api/admin-global/backup", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_backup():
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_dir = f"backups/backup_{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            sql_file = os.path.join(backup_dir, "database.sql")
            cmd = [
                'mysqldump',
                f'--host={Config.MYSQL_HOST}',
                f'--user={Config.MYSQL_USER}',
                f'--password={Config.MYSQL_PASSWORD}',
                Config.MYSQL_DB,
                '--result-file=' + sql_file
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if os.path.exists(upload_folder):
                shutil.copytree(upload_folder, os.path.join(backup_dir, 'uploads'), dirs_exist_ok=True)

            log_entry = Log(
                user_id=request.user_id,
                action='BACKUP_MANUAL',
                description=f"Sauvegarde créée: {backup_dir}",
                date_action=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({"success": True, "message": f"Sauvegarde effectuée dans {backup_dir}"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_backup: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # STATISTIQUES ÉVOLUTION
    # ============================================

    @app.route("/api/admin-global/stats/evolution", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_stats_evolution():
        try:
            from sqlalchemy import func
            rows = db.session.query(
                func.date(Document.date_creation).label('date_jour'),
                func.count(Document.id).label('total')
            ).filter(
                Document.date_creation >= datetime.utcnow() - timedelta(weeks=8)
            ).group_by(func.date(Document.date_creation)).order_by(func.date(Document.date_creation).asc()).all()

            labels = [row.date_jour.isoformat() for row in rows]
            data = [row.total for row in rows]
            return jsonify({"success": True, "labels": labels, "data": data}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_stats_evolution: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
