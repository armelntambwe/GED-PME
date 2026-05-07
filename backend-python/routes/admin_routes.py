# routes/admin_routes.py - Version corrigee sans doublons

from flask import request, jsonify, send_file
from middleware.auth import token_required, role_required
from utils.db import get_db
import csv
from datetime import datetime
import os
import subprocess
import shutil
from config import Config

def register_admin_routes(app):

    # ============================================
    # STATISTIQUES
    # ============================================
    
    @app.route("/api/admin-global/stats", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_stats():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as total FROM entreprises")
            entreprises = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as total FROM users")
            users = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as total FROM documents WHERE supprime_le IS NULL OR supprime_le = ''")
            documents = cur.fetchone()['total']
            cur.close()
            conn.close()
            return jsonify({"success": True, "stats": {"entreprises": entreprises or 0, "users": users or 0, "documents": documents or 0}}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # DÉSACTIVER / RÉACTIVER UN UTILISATEUR
    # ============================================
    @app.route("/api/admin-global/users/<int:user_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_toggle_user(user_id):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT actif, nom FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            
            new_status = 0 if user['actif'] == 1 else 1
            cur.execute("UPDATE users SET actif = %s WHERE id = %s", (new_status, user_id))
            
            status_text = "activé" if new_status == 1 else "désactivé"
            cur.execute("""
                INSERT INTO notifications (user_id, type, message, lien, lue, date_creation)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (request.user_id, 'USER_TOGGLE', f"L'utilisateur {user['nom']} a été {status_text}", f"/dashboard-admin-global?tab=users", datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"success": True, "message": f"Utilisateur {status_text}"}), 200
        except Exception as e:
            print(f"[ERREUR] admin_global_toggle_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # RÉINITIALISER MOT DE PASSE UTILISATEUR
    # ============================================
    @app.route("/api/admin-global/users/<int:user_id>/reset-password", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_reset_password(user_id):
        try:
            from werkzeug.security import generate_password_hash
            data = request.json
            new_password = data.get('password', 'employe123')
            password_hash = generate_password_hash(new_password)
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT nom FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            
            cur.execute("UPDATE users SET password = %s WHERE id = %s", (password_hash, user_id))
            
            cur.execute("""
                INSERT INTO notifications (user_id, type, message, lien, lue, date_creation)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (request.user_id, 'PASSWORD_RESET', f"Le mot de passe de l'utilisateur {user['nom']} a été réinitialisé", f"/dashboard-admin-global?tab=users", datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"success": True, "message": f"Mot de passe réinitialisé à {new_password}"}), 200
        except Exception as e:
            print(f"[ERREUR] admin_global_reset_password: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # SUPPRIMER UNE ENTREPRISE (soft delete)
    # ============================================
    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/delete", methods=["DELETE"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_delete_entreprise(entreprise_id):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT nom, statut FROM entreprises WHERE id = %s", (entreprise_id,))
            ent = cur.fetchone()
            if not ent:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            
            cur.execute("UPDATE entreprises SET statut = 'suspendu' WHERE id = %s", (entreprise_id,))
            
            cur.execute("""
                INSERT INTO notifications (user_id, type, message, lien, lue, date_creation)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (request.user_id, 'ENTREPRISE_SUPPRIMEE', f"L'entreprise {ent['nom']} a été supprimée (soft delete)", f"/dashboard-admin-global?tab=entreprises", datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"success": True, "message": "Entreprise supprimée (soft delete)"}), 200
        except Exception as e:
            print(f"[ERREUR] admin_global_delete_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # EXPORT ENTREPRISES CSV
    # ============================================
    @app.route("/api/admin-global/entreprises/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_export_entreprises():
        try:
            from io import BytesIO
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nom, email, telephone, adresse, statut, date_creation,
                       (SELECT COUNT(*) FROM users WHERE entreprise_id = entreprises.id) as nb_employes,
                       (SELECT COUNT(*) FROM documents WHERE entreprise_id = entreprises.id) as nb_documents
                FROM entreprises
                ORDER BY id DESC
            """)
            entreprises = cur.fetchall()
            cur.close()
            conn.close()
            
            output = BytesIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(['ID', 'Nom', 'Email', 'Telephone', 'Adresse', 'Statut', 'Date creation', 'Employes', 'Documents'])
            for e in entreprises:
                writer.writerow([
                    str(e['id']), 
                    e['nom'], 
                    e['email'] or '', 
                    e['telephone'] or '', 
                    e['adresse'] or '', 
                    e['statut'], 
                    str(e['date_creation']) if e['date_creation'] else '', 
                    str(e['nb_employes'] or 0), 
                    str(e['nb_documents'] or 0)
                ])
            
            output.seek(0)
            return send_file(
                output, 
                as_attachment=True, 
                download_name=f"entreprises_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mimetype='text/csv'
            )
        except Exception as e:
            print(f"[ERREUR] export_entreprises: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # EXPORT UTILISATEURS CSV
    # ============================================
    @app.route("/api/admin-global/users/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_export_users():
        try:
            from io import BytesIO
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.nom, u.email, u.telephone, u.role, u.actif, u.date_inscription, e.nom as entreprise_nom
                FROM users u
                LEFT JOIN entreprises e ON e.id = u.entreprise_id
                ORDER BY u.id DESC
            """)
            users = cur.fetchall()
            cur.close()
            conn.close()
            
            output = BytesIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(['ID', 'Nom', 'Email', 'Telephone', 'Role', 'Actif', 'Date inscription', 'Entreprise'])
            for u in users:
                writer.writerow([
                    str(u['id']), 
                    u['nom'], 
                    u['email'] or '', 
                    u['telephone'] or '', 
                    u['role'], 
                    'Actif' if u['actif'] else 'Inactif', 
                    str(u['date_inscription']) if u['date_inscription'] else '', 
                    u['entreprise_nom'] or ''
                ])
            
            output.seek(0)
            return send_file(
                output, 
                as_attachment=True, 
                download_name=f"utilisateurs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mimetype='text/csv'
            )
        except Exception as e:
            print(f"[ERREUR] export_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
        
    # ============================================
    # FILTRE LOGS PAR DATE
    # ============================================
    @app.route("/api/admin-global/logs/filter", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_filter_logs():
        try:
            date_debut = request.args.get('date_debut')
            date_fin = request.args.get('date_fin')
            action = request.args.get('action')
            
            conn = get_db()
            cur = conn.cursor()
            
            query = """
                SELECT l.date_action, l.action, l.description, u.nom as utilisateur_nom
                FROM logs l
                LEFT JOIN users u ON u.id = l.user_id
                WHERE 1=1
            """
            params = []
            
            if date_debut:
                query += " AND DATE(l.date_action) >= %s"
                params.append(date_debut)
            if date_fin:
                query += " AND DATE(l.date_action) <= %s"
                params.append(date_fin)
            if action:
                query += " AND l.action = %s"
                params.append(action)
            
            query += " ORDER BY l.date_action DESC LIMIT 500"
            
            cur.execute(query, params)
            logs = cur.fetchall()
            cur.close()
            conn.close()
            
            for log in logs:
                if log.get('date_action'):
                    log['date_action'] = str(log['date_action'])
            
            return jsonify({"success": True, "logs": logs}), 200
        except Exception as e:
            print(f"[ERREUR] admin_global_filter_logs: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # ENTREPRISES (CRUD)
    # ============================================
    
    @app.route("/api/admin-global/entreprises", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_entreprises():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT e.*, 
                       (SELECT COUNT(*) FROM users WHERE entreprise_id = e.id AND role = 'employe') as nb_employes,
                       (SELECT COUNT(*) FROM documents WHERE entreprise_id = e.id) as nb_documents
                FROM entreprises e
                ORDER BY e.id DESC
            """)
            entreprises = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({"success": True, "entreprises": entreprises}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_create_entreprise():
        try:
            data = request.json
            if not data.get('nom'):
                return jsonify({"success": False, "message": "Nom requis"}), 400
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO entreprises (nom, email, telephone, adresse, statut)
                VALUES (%s, %s, %s, %s, 'actif')
            """, (data.get('nom'), data.get('email'), data.get('telephone'), data.get('adresse')))
            entreprise_id = cur.lastrowid
            
            cur.execute("""
                INSERT INTO notifications (user_id, type, message, lien, lue, date_creation)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (request.user_id, 'ENTREPRISE_CREEE', f"L'entreprise {data.get('nom')} a été créée", f"/dashboard-admin-global?tab=entreprises", datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Entreprise créée", "entreprise_id": entreprise_id}), 201
        except Exception as e:
            print(f"[ERREUR] admin_global_create_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_update_entreprise(entreprise_id):
        try:
            data = request.json
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("SELECT nom FROM entreprises WHERE id = %s", (entreprise_id,))
            old_nom = cur.fetchone()['nom']
            
            cur.execute("""
                UPDATE entreprises 
                SET nom = %s, email = %s, telephone = %s, adresse = %s
                WHERE id = %s
            """, (data.get('nom'), data.get('email'), data.get('telephone'), data.get('adresse'), entreprise_id))
            
            cur.execute("""
                INSERT INTO notifications (user_id, type, message, lien, lue, date_creation)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (request.user_id, 'ENTREPRISE_MODIFIEE', f"L'entreprise {old_nom} a été modifiée", f"/dashboard-admin-global?tab=entreprises", datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Entreprise modifiée"}), 200
        except Exception as e:
            print(f"[ERREUR] admin_global_update_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/entreprises/<int:entreprise_id>/toggle", methods=["PUT"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_toggle_entreprise(entreprise_id):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT nom, statut FROM entreprises WHERE id = %s", (entreprise_id,))
            ent = cur.fetchone()
            if not ent:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            
            new_status = 'suspendu' if ent['statut'] == 'actif' else 'actif'
            cur.execute("UPDATE entreprises SET statut = %s WHERE id = %s", (new_status, entreprise_id))
            
            cur.execute("""
                INSERT INTO notifications (user_id, type, message, lien, lue, date_creation)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (request.user_id, 'ENTREPRISE_TOGGLE', f"L'entreprise {ent['nom']} est maintenant {new_status}", f"/dashboard-admin-global?tab=entreprises", datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": f"Statut changé en {new_status}"}), 200
        except Exception as e:
            print(f"[ERREUR] admin_global_toggle_entreprise: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # UTILISATEURS
    # ============================================
    
    @app.route("/api/admin-global/all-users", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_users():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.nom, u.email, u.role, u.actif, e.nom as entreprise_nom
                FROM users u
                LEFT JOIN entreprises e ON e.id = u.entreprise_id
                ORDER BY u.id DESC
            """)
            users = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({"success": True, "users": users}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # DOCUMENTS
    # ============================================
    
    @app.route("/api/admin-global/all-documents", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_documents():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT d.id, d.titre, d.date_creation, u.nom as auteur_nom, e.nom as entreprise_nom
                FROM documents d
                LEFT JOIN users u ON u.id = d.auteur_id
                LEFT JOIN entreprises e ON e.id = d.entreprise_id
                WHERE d.supprime_le IS NULL OR d.supprime_le = ''
                ORDER BY d.date_creation DESC
                LIMIT 100
            """)
            documents = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({"success": True, "documents": documents}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # LOGS
    # ============================================
    
    @app.route("/api/admin-global/all-logs", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_all_logs():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT l.date_action, l.action, l.description, u.nom as utilisateur_nom
                FROM logs l
                LEFT JOIN users u ON u.id = l.user_id
                ORDER BY l.date_action DESC
                LIMIT 200
            """)
            logs = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({"success": True, "logs": logs}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/admin-global/logs/export", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_logs_export():
        try:
            from io import BytesIO
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT date_action, action, description, (SELECT nom FROM users WHERE id = logs.user_id) as utilisateur_nom
                FROM logs
                ORDER BY date_action DESC
                LIMIT 1000
            """)
            logs = cur.fetchall()
            cur.close()
            conn.close()
            
            output = BytesIO()
            writer = csv.writer(output)
            writer.writerow(['Date', 'Action', 'Description', 'Utilisateur'])
            for log in logs:
                writer.writerow([
                    str(log['date_action']) if log['date_action'] else '',
                    log['action'],
                    log['description'] or '',
                    log['utilisateur_nom'] or ''
                ])
            
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mimetype='text/csv')
        except Exception as e:
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
            return jsonify({"success": True, "storage": {"used_mb": used_mb, "total_mb": total_mb, "used_gb": used_gb, "total_gb": total_gb, "free_gb": free_gb, "uploads_mb": used_mb, "percent": round((used_mb / total_mb) * 100, 1)}}), 200
        except Exception as e:
            return jsonify({"success": True, "storage": {"used_mb": 0, "total_mb": 1024, "used_gb": 0, "total_gb": 1, "free_gb": 1, "uploads_mb": 0, "percent": 0}}), 200

    # ============================================
    # BACKUP
    # ============================================
    
    @app.route("/api/admin-global/backup", methods=["POST"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_backup():
        try:
            import subprocess, shutil, os
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
                shutil.copytree(upload_folder, f"{backup_dir}/uploads", dirs_exist_ok=True)
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO logs (user_id, action, description, date_action)
                VALUES (%s, 'BACKUP_MANUAL', %s, NOW())
            """, (request.user_id, f"Sauvegarde créée: {backup_dir}"))
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": f"Sauvegarde effectuée dans {backup_dir}"}), 200
        except Exception as e:
            print(f"[ERREUR] backup: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    # ============================================
    # STATISTIQUES ÉVOLUTION
    # ============================================
    
    @app.route("/api/admin-global/stats/evolution", methods=["GET"])
    @token_required
    @role_required(['admin_global'])
    def admin_global_stats_evolution():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT DATE_FORMAT(date_creation, '%Y-%m-%d') as date_jour, COUNT(*) as total
                FROM documents
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL 8 WEEK)
                GROUP BY DATE(date_creation)
                ORDER BY date_jour ASC
            """)
            results = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({"success": True, "labels": [r['date_jour'] for r in results], "data": [r['total'] for r in results]}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500