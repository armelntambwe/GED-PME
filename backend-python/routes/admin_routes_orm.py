"""
Routes administrateur refactorisées - ORM SQLAlchemy pur (sans SQL brut)
Remplace progressivement admin_routes.py
"""
from extensions import db
from flask import request, jsonify, send_file
from middleware.auth import token_required, role_required
from services.user_service import UserService
from services.admin_service_orm import AdminService
from werkzeug.security import generate_password_hash
import csv
import logging
from datetime import datetime
from io import BytesIO, StringIO

logger = logging.getLogger(__name__)


def register_admin_routes_orm(app):
    """Enregistre les routes administrateur avec services ORM."""
    
    # ============================================
    # STATISTIQUES GLOBALES
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

    @app.route("/api/admin-global/stats/evolution", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_stats_evolution():
        try:
            from models_sqlalchemy import Document
            from sqlalchemy import func
            from datetime import datetime, timedelta
            
            eight_weeks_ago = datetime.utcnow() - timedelta(weeks=8)
            
            results = db.session.query(
                func.date(Document.date_creation).label('date_jour'),
                func.count(Document.id).label('total')
            ).filter(Document.date_creation >= eight_weeks_ago).group_by(func.date(Document.date_creation)).order_by('date_jour').all()
            
            labels = [str(r.date_jour) for r in results]
            data = [r.total for r in results]
            
            return jsonify({"success": True, "labels": labels, "data": data}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_stats_evolution: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # GESTION ENTREPRISES
    # ============================================
    
    @app.route("/api/admin-global/entreprises", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_entreprises():
        try:
            companies = AdminService.list_all_companies()
            return jsonify({"success": True, "entreprises": companies}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_entreprises: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_create_entreprise():
        try:
            from models_sqlalchemy import Entreprise
            data = request.json
            
            if not data.get('nom'):
                return jsonify({"success": False, "message": "Le nom est requis"}), 400
            
            entreprise = Entreprise(
                nom=data['nom'],
                email=data.get('email', ''),
                telephone=data.get('telephone', ''),
                adresse=data.get('adresse', ''),
                statut='actif'
            )
            db.session.add(entreprise)
            db.session.commit()
            
            return jsonify({"success": True, "message": "Entreprise créée", "id": entreprise.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_create_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_update_entreprise(entreprise_id):
        try:
            from models_sqlalchemy import Entreprise
            data = request.json
            
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            
            if 'nom' in data:
                entreprise.nom = data['nom']
            if 'adresse' in data:
                entreprise.adresse = data['adresse']
            if 'telephone' in data:
                entreprise.telephone = data['telephone']
            if 'email' in data:
                entreprise.email = data['email']
            
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
            from models_sqlalchemy import Entreprise
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            
            entreprise.statut = 'suspendu' if entreprise.statut == 'actif' else 'actif'
            db.session.commit()
            return jsonify({"success": True, "message": f"Statut modifié"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_toggle_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/delete", methods=["DELETE"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_delete_entreprise(entreprise_id):
        try:
            from models_sqlalchemy import Entreprise
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            
            entreprise.statut = 'suspendu'
            db.session.commit()
            return jsonify({"success": True, "message": "Entreprise supprimée"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_delete_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # GESTION UTILISATEURS
    # ============================================
    
    @app.route("/api/admin-global/all-users", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_users():
        try:
            users = AdminService.list_all_users()
            return jsonify({"success": True, "users": users}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/<int:user_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_toggle_user(user_id):
        try:
            from models_sqlalchemy import User
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            
            user.actif = not user.actif
            db.session.commit()
            return jsonify({"success": True, "message": f"Utilisateur {'activé' if user.actif else 'désactivé'}"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_toggle_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/<int:user_id>/reset-password", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_reset_password(user_id):
        try:
            from models_sqlalchemy import User
            data = request.json
            password = data.get('password', 'employe123')
            
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            
            user.password = generate_password_hash(password)
            db.session.commit()
            return jsonify({"success": True, "message": f"Mot de passe réinitialisé à {password}"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_reset_password: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # DOCUMENTS GLOBAUX
    # ============================================
    
    @app.route("/api/admin-global/all-documents", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_documents():
        try:
            from models_sqlalchemy import Document
            documents = Document.query.filter(
                (Document.supprime_le.is_(None)) | (Document.supprime_le == '')
            ).order_by(Document.date_creation.desc()).limit(100).all()
            return jsonify({"success": True, "documents": [doc.to_dict() for doc in documents]}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_documents: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # LOGS GLOBAUX
    # ============================================
    
    @app.route("/api/admin-global/all-logs", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_logs():
        try:
            from models_sqlalchemy import Log
            logs = Log.query.order_by(Log.date_action.desc()).limit(200).all()
            return jsonify({"success": True, "logs": [log.to_dict() for log in logs]}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_logs: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/logs/filter", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_logs_filter():
        try:
            from models_sqlalchemy import Log
            date_debut = request.args.get('date_debut')
            date_fin = request.args.get('date_fin')
            action = request.args.get('action')
            
            query = Log.query
            if date_debut:
                query = query.filter(Log.date_action >= date_debut)
            if date_fin:
                query = query.filter(Log.date_action <= date_fin)
            if action:
                query = query.filter(Log.action == action)
            
            logs = query.order_by(Log.date_action.desc()).limit(500).all()
            return jsonify({"success": True, "logs": [log.to_dict() for log in logs]}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_logs_filter: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # STOCKAGE
    # ============================================
    
    @app.route("/api/admin-global/storage", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_storage():
        try:
            import os
            upload_folder = 'uploads'
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
            return jsonify({"success": True, "storage": {"used_mb": used_mb, "total_mb": total_mb, "used_gb": used_gb, "total_gb": total_gb, "free_gb": free_gb, "uploads_mb": used_mb, "percent": round((used_mb / total_mb) * 100, 1)}}), 200
        except Exception as e:
            return jsonify({"success": True, "storage": {"used_mb": 0, "total_mb": 1024, "used_gb": 0, "total_gb": 1, "free_gb": 1, "uploads_mb": 0, "percent": 0}}), 200

    @app.route("/api/admin-global/backup", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_backup():
        try:
            import subprocess
            import os
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = "backups"
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            backup_file_abs = os.path.abspath(backup_file)
            
            # Chemin exact de mysqldump
            mysqldump_path = r"C:\xampp\mysql\bin\mysqldump.exe"
            
            # Commande avec result-file
            cmd = [
                mysqldump_path,
                "-u", "root",
                "ged_pme",
                f"--result-file={backup_file_abs}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(backup_file_abs) and os.path.getsize(backup_file_abs) > 0:
                return jsonify({"success": True, "message": f"Sauvegarde effectuee: {backup_file}"}), 200
            else:
                return jsonify({"success": False, "message": f"Erreur: {result.stderr}"}), 500
                
        except Exception as e:
            print(f"[ERREUR] backup: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    # EXPORTS CSV
    # ============================================
    
    @app.route("/api/admin-global/entreprises/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_entreprises_export():
        try:
            companies = AdminService.list_all_companies(limit=10000)
            
            output_text = StringIO()
            writer = csv.writer(output_text, quoting=csv.QUOTE_ALL)
            writer.writerow(['ID', 'Nom', 'Email', 'Telephone', 'Adresse', 'Statut', 'Date Creation'])
            
            for c in companies:
                writer.writerow([
                    str(c.get('id', '')), 
                    str(c.get('nom', '')), 
                    str(c.get('email', '')),
                    str(c.get('telephone', '')), 
                    str(c.get('adresse', '')),
                    str(c.get('statut', '')), 
                    str(c.get('date_creation', ''))
                ])
            
            bytes_out = BytesIO(output_text.getvalue().encode('utf-8-sig'))
            bytes_out.seek(0)
            
            return send_file(
                bytes_out,
                as_attachment=True,
                download_name=f"entreprises_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mimetype='text/csv'
            )
        except Exception as e:
            logger.error(f"Erreur admin_global_entreprises_export: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_users_export():
        try:
            users = AdminService.list_all_users(limit=10000)
            
            output_text = StringIO()
            writer = csv.writer(output_text, quoting=csv.QUOTE_ALL)
            writer.writerow(['ID', 'Nom', 'Email', 'Telephone', 'Role', 'Actif', 'Date Inscription', 'Entreprise'])
            
            for u in users:
                writer.writerow([
                    str(u.get('id', '')), 
                    str(u.get('nom', '')), 
                    str(u.get('email', '')),
                    str(u.get('telephone', '')), 
                    str(u.get('role', '')),
                    'Oui' if u.get('actif') else 'Non',
                    str(u.get('date_inscription', '')), 
                    str(u.get('entreprise_nom', ''))
                ])
            
            bytes_out = BytesIO(output_text.getvalue().encode('utf-8-sig'))
            bytes_out.seek(0)
            
            return send_file(
                bytes_out,
                as_attachment=True,
                download_name=f"utilisateurs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mimetype='text/csv'
            )
        except Exception as e:
            logger.error(f"Erreur admin_global_users_export: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/logs/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_logs_export():
        try:
            from models_sqlalchemy import Log
            logs = Log.query.order_by(Log.date_action.desc()).limit(1000).all()
            
            output_text = StringIO()
            writer = csv.writer(output_text, quoting=csv.QUOTE_ALL)
            writer.writerow(['Date', 'Action', 'Description', 'Utilisateur'])
            
            for log in logs:
                writer.writerow([
                    log.date_action.isoformat() if log.date_action else '',
                    log.action or '',
                    log.description or '',
                    log.user.nom if log.user else ''
                ])
            
            bytes_out = BytesIO(output_text.getvalue().encode('utf-8-sig'))
            bytes_out.seek(0)
            
            return send_file(
                bytes_out,
                as_attachment=True,
                download_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mimetype='text/csv'
            )
        except Exception as e:
            logger.error(f"Erreur admin_global_logs_export: {e}")
            return jsonify({"success": False, "message": str(e)}), 500