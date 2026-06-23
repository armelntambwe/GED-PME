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
import json
import logging
import os
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
            from utils.company_logo import save_company_logo

            if request.content_type and 'multipart/form-data' in request.content_type:
                entreprise = json.loads(request.form.get('entreprise', '{}'))
                administrateur = json.loads(request.form.get('administrateur', '{}'))
                logo_file = request.files.get('logo')
                create_admin = bool(administrateur.get('email'))
            else:
                data = request.json or {}
                administrateur = data.get('administrateur')
                entreprise = {k: v for k, v in data.items() if k != 'administrateur'}
                logo_file = None
                create_admin = bool(administrateur and administrateur.get('email'))

            if create_admin and administrateur:
                required = ['nom', 'nif', 'rccm', 'adresse', 'telephone', 'email']
                missing = [f for f in required if not (entreprise.get(f) or '').strip()]
                if missing:
                    return jsonify({"success": False, "message": "Champs entreprise manquants: " + ', '.join(missing)}), 400
                if not administrateur.get('nom') or not administrateur.get('email') or not administrateur.get('password'):
                    return jsonify({"success": False, "message": "Admin PME: nom, email et mot de passe requis"}), 400
                administrateur['password'] = generate_password_hash(administrateur['password'])
                result = AdminService.create_company_with_admin(entreprise, administrateur)
                if not result.get('success'):
                    return jsonify({"success": False, "message": result.get('message')}), result.get('status_code', 400)
                entreprise_id = result['entreprise_id']
                if logo_file and logo_file.filename:
                    logo_url = save_company_logo(entreprise_id, logo_file)
                    if logo_url:
                        company = Entreprise.query.get(entreprise_id)
                        if company:
                            company.logo_url = logo_url
                            db.session.commit()
                return jsonify({"success": True, "message": "Entreprise et admin PME créés", "id": entreprise_id}), 201

            if not entreprise.get('nom'):
                return jsonify({"success": False, "message": "Le nom est requis"}), 400

            ent = Entreprise(
                nom=entreprise['nom'],
                nif=(entreprise.get('nif') or '').strip(),
                rccm=(entreprise.get('rccm') or '').strip(),
                secteur_activite=(entreprise.get('secteur_activite') or '').strip(),
                email=entreprise.get('email', ''),
                telephone=entreprise.get('telephone', ''),
                adresse=entreprise.get('adresse', ''),
                statut='actif'
            )
            db.session.add(ent)
            db.session.commit()
            from services.category_service import CategoryService
            CategoryService.seed_default_categories(ent.id)
            if logo_file and logo_file.filename:
                logo_url = save_company_logo(ent.id, logo_file)
                if logo_url:
                    ent.logo_url = logo_url
                    db.session.commit()
            return jsonify({"success": True, "message": "Entreprise créée", "id": ent.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_create_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_entreprise_detail(entreprise_id):
        try:
            detail = AdminService.get_company_detail(entreprise_id)
            if not detail:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            return jsonify({"success": True, "entreprise": detail}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_entreprise_detail: {e}")
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
            if 'nif' in data:
                entreprise.nif = data['nif']
            if 'rccm' in data:
                entreprise.rccm = data['rccm']
            if 'secteur_activite' in data:
                entreprise.secteur_activite = data['secteur_activite']
            if 'statut' in data:
                entreprise.statut = data['statut']
            
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
            hard = request.args.get('hard', '').lower() in ('1', 'true', 'yes')
            if hard:
                result = AdminService.hard_delete_company(entreprise_id)
                status = 200 if result.get('success') else 400
                return jsonify(result), status

            from models_sqlalchemy import Entreprise
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

            entreprise.statut = 'suspendu'
            db.session.commit()
            return jsonify({"success": True, "message": "Entreprise suspendue"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur admin_global_delete_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/workflow", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_get_workflow(entreprise_id):
        try:
            config = AdminService.get_workflow_config(entreprise_id)
            return jsonify({"success": True, "etapes": config}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/workflow", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_save_workflow(entreprise_id):
        try:
            data = request.json or {}
            etapes = data.get('etapes', [])
            AdminService.save_workflow_config(entreprise_id, etapes)
            return jsonify({"success": True, "message": "Workflow enregistré"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # GESTION UTILISATEURS
    # ============================================
    
    @app.route("/api/admin-global/all-users", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_users():
        try:
            role = request.args.get('role')
            entreprise_id = request.args.get('entreprise_id', type=int)
            actif = request.args.get('actif')
            search = request.args.get('search')
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 500, type=int)

            if role or entreprise_id or actif or search or page > 1 or limit < 5000:
                result = AdminService.list_users_filtered(
                    role=role, entreprise_id=entreprise_id, actif=actif,
                    search=search, page=page, limit=limit,
                )
                return jsonify({"success": True, **result}), 200

            from models_sqlalchemy import User
            users = User.query.order_by(User.id.desc()).limit(5000).all()
            result = []
            for user in users:
                data = user.to_dict()
                data['entreprise_nom'] = user.entreprise.nom if user.entreprise else None
                result.append(data)
            return jsonify({"success": True, "users": result}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_create_user():
        try:
            data = request.json or {}
            nom = (data.get('nom') or '').strip()
            email = (data.get('email') or '').strip()
            password = data.get('password') or ''
            role = data.get('role', 'employe')
            entreprise_id = data.get('entreprise_id')
            telephone = data.get('telephone', '')

            if not nom or not email or not password:
                return jsonify({"success": False, "message": "Nom, email et mot de passe requis"}), 400
            if role in ('employe', 'admin_pme') and not entreprise_id:
                return jsonify({"success": False, "message": "Entreprise requise pour ce rôle"}), 400
            if len(password) < 6:
                return jsonify({"success": False, "message": "Mot de passe min. 6 caractères"}), 400

            existing = UserService.get_user_by_email_raw(email)
            if existing:
                return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

            user_id = UserService.create_user(
                nom, email, generate_password_hash(password), role,
                telephone=telephone, entreprise_id=entreprise_id if role != 'admin_global' else None,
            )
            return jsonify({"success": True, "message": "Utilisateur créé", "id": user_id}), 201
        except Exception as e:
            logger.error(f"Erreur admin_global_create_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/<int:user_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_update_user(user_id):
        try:
            from models_sqlalchemy import User
            data = request.json or {}
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            if user_id == request.user_id and data.get('role') and data['role'] != user.role:
                return jsonify({"success": False, "message": "Vous ne pouvez pas changer votre propre rôle"}), 400

            if 'nom' in data:
                user.nom = data['nom']
            if 'telephone' in data:
                user.telephone = data['telephone']
            if 'role' in data:
                user.role = data['role']
            if 'entreprise_id' in data:
                new_role = data.get('role', user.role)
                user.entreprise_id = data['entreprise_id'] if new_role != 'admin_global' else None
            if 'actif' in data:
                user.actif = bool(data['actif'])

            db.session.commit()
            return jsonify({"success": True, "message": "Utilisateur mis à jour"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/users/<int:user_id>", methods=["DELETE"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_delete_user(user_id):
        try:
            result = AdminService.delete_user(user_id, request.user_id)
            status = result.pop('status', 200 if result.get('success') else 400)
            return jsonify(result), status
        except Exception as e:
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
            search = request.args.get('search')
            statut = request.args.get('statut')
            entreprise_id = request.args.get('entreprise_id', type=int)
            extension = request.args.get('extension')
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 25, type=int)

            result = AdminService.list_global_documents(
                search=search, statut=statut, entreprise_id=entreprise_id,
                extension=extension, page=page, limit=limit,
            )
            return jsonify({"success": True, **result}), 200
        except Exception as e:
            logger.error(f"Erreur admin_global_all_documents: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/documents/pending", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_pending_documents():
        try:
            docs = AdminService.list_pending_validation_documents(limit=200)
            return jsonify({"success": True, "documents": docs}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/activity", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_activity():
        try:
            limit = request.args.get('limit', 100, type=int)
            entreprise_id = request.args.get('entreprise_id', type=int)
            report = AdminService.get_user_activity_report(limit=limit, entreprise_id=entreprise_id)
            return jsonify({"success": True, "activity": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/settings", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_settings_get():
        try:
            settings = AdminService.get_platform_settings_view()
            health = AdminService.get_platform_health()
            return jsonify({"success": True, "settings": settings, "health": health}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/settings/maintenance", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_settings_maintenance():
        try:
            from utils.platform_settings import save_platform_settings
            data = request.json or {}
            updated = save_platform_settings({
                'maintenance_mode': bool(data.get('maintenance_mode')),
                'maintenance_message': data.get('maintenance_message') or 'Maintenance en cours.',
            })
            return jsonify({"success": True, "settings": updated}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/backups", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_list_backups():
        try:
            backups = AdminService.list_backups()
            return jsonify({"success": True, "backups": backups}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/backups/<path:filename>", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_download_backup(filename):
        try:
            if '..' in filename or '/' in filename or '\\' in filename:
                return jsonify({"success": False, "message": "Nom de fichier invalide"}), 400
            backup_dir = os.path.abspath("backups")
            filepath = os.path.join(backup_dir, filename)
            if not filepath.startswith(backup_dir) or not os.path.isfile(filepath):
                return jsonify({"success": False, "message": "Fichier introuvable"}), 404
            return send_file(filepath, as_attachment=True, download_name=filename)
        except Exception as e:
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
            
            from config import Config
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = "backups"

            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            backup_file_abs = os.path.abspath(backup_file)

            mysqldump_paths = [
                r"C:\xampp\mysql\bin\mysqldump.exe",
                r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
                "mysqldump",
            ]
            mysqldump_path = next((p for p in mysqldump_paths if p == "mysqldump" or os.path.isfile(p)), "mysqldump")

            cmd = [
                mysqldump_path,
                "-h", Config.MYSQL_HOST,
                "-u", Config.MYSQL_USER,
            ]
            if Config.MYSQL_PASSWORD:
                cmd.extend(["-p" + Config.MYSQL_PASSWORD])
            cmd.extend([Config.MYSQL_DB, f"--result-file={backup_file_abs}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(backup_file_abs) and os.path.getsize(backup_file_abs) > 0:
                return jsonify({"success": True, "message": f"Sauvegarde effectuee: {backup_file}", "filename": os.path.basename(backup_file)}), 200
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