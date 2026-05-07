# routes/user_routes.py
from flask import request, jsonify
from middleware.auth import token_required, role_required
from models.user import User
from models.log import Log
from models.notification import Notification
from werkzeug.security import generate_password_hash
from utils.db import get_db

def register_user_routes(app):

    @app.route("/users", methods=["GET"])
    @token_required
    def get_users():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id, nom, email, role, actif, entreprise_id FROM users ORDER BY id DESC")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            users = []
            for row in rows:
                users.append({
                    'id': row[0],
                    'nom': row[1],
                    'email': row[2],
                    'role': row[3],
                    'actif': row[4],
                    'entreprise_id': row[5]
                })
            
            return jsonify({"success": True, "users": users}), 200
        except Exception as e:
            print(f"[ERREUR] get_users: {e}")
            return jsonify({"success": True, "users": []}), 200

    @app.route("/users/<int:user_id>/desactiver", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def desactiver_user(user_id):
        User.deactivate(user_id)
        Log.create('DESACTIVATION_USER', f"Utilisateur {user_id} désactivé", request.user_id)
        
        Notification.create(
            user_id=request.user_id,
            type_notif='USER_DESACTIVE',
            message=f"L'utilisateur a été désactivé",
            lien='/dashboard-pme?tab=employes'
        )
        
        return jsonify({"success": True, "message": "Utilisateur désactivé"}), 200

    @app.route("/admin/employes", methods=["GET"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def get_employes():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            print(f"[DEBUG] get_employes - entreprise_id reçu: {entreprise_id}")
            
            conn = get_db()
            cur = conn.cursor()
            
            query = "SELECT id, nom, email, telephone, actif FROM users WHERE role = 'employe'"
            params = []
            
            if entreprise_id is not None:
                query += " AND entreprise_id = %s"
                params.append(entreprise_id)
            
            query += " ORDER BY id DESC"
            
            print(f"[DEBUG] Requête SQL: {query}")
            print(f"[DEBUG] Paramètres: {params}")
            
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            print(f"[DEBUG] Nombre d'employés trouvés: {len(rows)}")
            
            result = []
            for row in rows:
                result.append({
                    'id': row[0],
                    'nom': row[1],
                    'email': row[2],
                    'telephone': row[3] if row[3] else '',
                    'actif': row[4]
                })
            
            print(f"[DEBUG] Résultat: {len(result)} employés retournés")
            
            return jsonify({"success": True, "employes": result}), 200
        except Exception as e:
            print(f"[ERREUR] get_employes: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": True, "employes": []}), 200

    @app.route("/admin/employes", methods=["POST"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def create_employe():
        try:
            data = request.json

            if not data or "nom" not in data or "email" not in data:
                return jsonify({"success": False, "message": "Nom et email requis"}), 400

            nom = data["nom"]
            email = data["email"]
            telephone = data.get("telephone", "")
            password = data.get("password", "employe123")
            password_hash = generate_password_hash(password)
            entreprise_id = getattr(request, 'user_entreprise_id', 1)

            print(f"[DEBUG] create_employe - entreprise_id: {entreprise_id}")

            existing_user = User.find_by_email(email)
            if existing_user:
                return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

            user_id = User.create(nom, email, password_hash, 'employe', telephone, entreprise_id)

            Log.create('CREATION_EMPLOYE', f"Employé '{nom}' créé", request.user_id)
            
            Notification.create(
                user_id=request.user_id,
                type_notif='EMPLOYE_CREE',
                message=f"L'employé {nom} a été créé",
                lien='/dashboard-pme?tab=employes'
            )

            return jsonify({
                "success": True,
                "message": "Employé créé",
                "user_id": user_id
            }), 201
        except Exception as e:
            print(f"[ERREUR] create_employe: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/info", methods=["GET"])
    @token_required
    def get_api_entreprise_info():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id, nom, adresse, telephone, email FROM entreprises WHERE id = %s", (entreprise_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row:
                return jsonify({
                    "success": True,
                    "id": row[0],
                    "nom": row[1],
                    "adresse": row[2] or '',
                    "telephone": row[3] or '',
                    "email": row[4] or ''
                }), 200
            else:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
        except Exception as e:
            print(f"[ERREUR] get_api_entreprise_info: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/info", methods=["PUT"])
    @token_required
    def update_api_entreprise_info():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            data = request.json
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE entreprises SET nom = %s, adresse = %s, telephone = %s, email = %s WHERE id = %s", 
                       (data.get('nom'), data.get('adresse'), data.get('telephone'), data.get('email'), entreprise_id))
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Entreprise mise à jour"}), 200
        except Exception as e:
            print(f"[ERREUR] update_api_entreprise_info: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/profile", methods=["GET"])
    @token_required
    def get_api_user_profile():
        try:
            user_id = request.user_id
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id, nom, email, telephone, role, actif FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row:
                return jsonify({
                    "success": True,
                    "id": row[0],
                    "nom": row[1],
                    "email": row[2],
                    "telephone": row[3] or '',
                    "role": row[4],
                    "actif": row[5]
                }), 200
            else:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
        except Exception as e:
            print(f"[ERREUR] get_api_user_profile: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/profile", methods=["PUT"])
    @token_required
    def update_api_user_profile():
        try:
            data = request.json
            nom = data.get('nom')
            telephone = data.get('telephone')
            password = data.get('password')
            
            conn = get_db()
            cur = conn.cursor()
            
            if nom:
                cur.execute("UPDATE users SET nom = %s WHERE id = %s", (nom, request.user_id))
            if telephone:
                cur.execute("UPDATE users SET telephone = %s WHERE id = %s", (telephone, request.user_id))
            if password:
                cur.execute("UPDATE users SET password = %s WHERE id = %s", (generate_password_hash(password), request.user_id))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Profil mis à jour"}), 200
        except Exception as e:
            print(f"[ERREUR] update_api_user_profile: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/logs", methods=["GET"])
    @token_required
    @role_required(['admin_pme'])
    def get_api_entreprise_logs():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT l.id, l.action, l.details, l.user_id, l.created_at, u.nom as user_nom, u.email as user_email
                FROM logs l
                JOIN users u ON l.user_id = u.id
                WHERE u.entreprise_id = %s
                ORDER BY l.created_at DESC
                LIMIT 50
            """, (entreprise_id,))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'action': row[1],
                    'details': row[2],
                    'user_id': row[3],
                    'created_at': str(row[4]) if row[4] else '',
                    'user_nom': row[5],
                    'user_email': row[6]
                })
            
            return jsonify({"success": True, "logs": logs}), 200
        except Exception as e:
            print(f"[ERREUR] get_api_entreprise_logs: {e}")
            return jsonify({"success": True, "logs": []}), 200