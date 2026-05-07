# app.py
from flask import Flask, send_from_directory, render_template, request, jsonify, send_file
from config import Config
from utils.db import get_db, test_connection
from middleware.auth import token_required, role_required
from werkzeug.security import generate_password_hash, check_password_hash
from utils.jwt_manager import generer_token

# AJOUT : Import des extensions SQLAlchemy
from extensions import db, migrate

# Routes imports
from routes.authentification_routes import register_authentification_routes
from routes.document_routes import register_document_routes
from routes.admin_routes import register_admin_routes
from routes.user_routes import register_user_routes
from routes.category_routes import register_category_routes
from routes.notification_routes import register_notification_routes
from routes.company_routes import register_company_routes

import os

app = Flask(__name__)
app.config.from_object(Config)

# AJOUT : Initialisation de SQLAlchemy et Alembic
db.init_app(app)
migrate.init_app(app, db)

# Test de connexion MySQL
print("Verification MySQL...")
success, message = test_connection()
print(f"{message}" if success else f"{message}")

# Enregistrement des routes
register_authentification_routes(app)
register_document_routes(app)
register_admin_routes(app)
register_user_routes(app)
register_category_routes(app)
register_notification_routes(app)
register_company_routes(app)

# ==============================
# FICHIERS STATIQUES
# ==============================

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js')

@app.route('/offline.html')
def serve_offline():
    return send_from_directory('static', 'offline.html')

@app.route('/offline-queue.js')
def serve_offline_queue():
    return send_from_directory('static', 'offline-queue.js')

# ==============================
# INTERFACES UTILISATEUR
# ==============================

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email et mot de passe requis"}), 400

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, password, role, entreprise_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401

        token = generer_token(user['id'], user['role'], user.get('entreprise_id'))

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user['id'],
                "nom": user['nom'],
                "role": user['role'],
                "entreprise_id": user.get('entreprise_id')
            }
        }), 200

    except Exception as e:
        print(f"[ERREUR] login_post: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/register-company')
def register_company_page():
    return render_template('register_company.html')

@app.route('/dashboard-admin-global')
def dashboard_admin_global():
    return render_template('dashboard-admin-global.html')

@app.route('/dashboard-pme')
def dashboard_pme():
    return render_template('dashboard-admin-pme.html')

@app.route('/dashboard-employee')
def dashboard_employee():
    return render_template('dashboard-employee.html')

# ============================================
# ROUTES API ADMIN PME (dans app.py)
# ============================================

@app.route("/api/pme/stats", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_stats():
    try:
        conn = get_db()
        cur = conn.cursor()
        entreprise_id = request.user_entreprise_id
        
        cur.execute("SELECT COUNT(*) as total FROM documents WHERE entreprise_id = %s", (entreprise_id,))
        total_documents = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM users WHERE entreprise_id = %s AND role = 'employe'", (entreprise_id,))
        total_employes = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM documents WHERE entreprise_id = %s AND statut = 'soumis'", (entreprise_id,))
        en_attente = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM documents WHERE entreprise_id = %s AND statut = 'valide'", (entreprise_id,))
        valides = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_documents": total_documents or 0,
                "total_employes": total_employes or 0,
                "en_attente": en_attente or 0,
                "valides": valides or 0
            }
        }), 200
    except Exception as e:
        print(f"[ERREUR] pme_stats: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/documents", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_documents():
    try:
        conn = get_db()
        cur = conn.cursor()
        entreprise_id = request.user_entreprise_id
        
        cur.execute("""
            SELECT d.*, u.nom as auteur_nom, c.nom as categorie_nom
            FROM documents d
            LEFT JOIN users u ON u.id = d.auteur_id
            LEFT JOIN categories c ON c.id = d.categorie_id
            WHERE d.entreprise_id = %s AND (d.supprime_le IS NULL OR d.supprime_le = '')
            ORDER BY d.date_creation DESC
        """, (entreprise_id,))
        
        documents = cur.fetchall()
        cur.close()
        conn.close()
        
        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])
        
        return jsonify({"success": True, "documents": documents}), 200
    except Exception as e:
        print(f"[ERREUR] pme_documents: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/employes", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_employes():
    try:
        conn = get_db()
        cur = conn.cursor()
        entreprise_id = request.user_entreprise_id
        
        cur.execute("""
            SELECT id, nom, email, telephone, role, actif, date_inscription
            FROM users
            WHERE entreprise_id = %s AND role = 'employe'
            ORDER BY id DESC
        """, (entreprise_id,))
        
        employes = cur.fetchall()
        cur.close()
        conn.close()
        
        for emp in employes:
            if emp.get('date_inscription'):
                emp['date_inscription'] = str(emp['date_inscription'])
        
        return jsonify({"success": True, "employes": employes}), 200
    except Exception as e:
        print(f"[ERREUR] pme_employes: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/validation", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_validation():
    try:
        conn = get_db()
        cur = conn.cursor()
        entreprise_id = request.user_entreprise_id
        
        cur.execute("""
            SELECT d.*, u.nom as auteur_nom
            FROM documents d
            LEFT JOIN users u ON u.id = d.auteur_id
            WHERE d.entreprise_id = %s AND d.statut = 'soumis' AND (d.supprime_le IS NULL OR d.supprime_le = '')
            ORDER BY d.date_creation DESC
        """, (entreprise_id,))
        
        documents = cur.fetchall()
        cur.close()
        conn.close()
        
        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])
        
        return jsonify({"success": True, "documents": documents}), 200
    except Exception as e:
        print(f"[ERREUR] pme_validation: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/corbeille", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_corbeille():
    try:
        conn = get_db()
        cur = conn.cursor()
        entreprise_id = request.user_entreprise_id
        
        cur.execute("""
            SELECT id, titre, supprime_le as date_suppression
            FROM documents
            WHERE entreprise_id = %s AND supprime_le IS NOT NULL AND supprime_le != ''
            ORDER BY supprime_le DESC
        """, (entreprise_id,))
        
        documents = cur.fetchall()
        cur.close()
        conn.close()
        
        for doc in documents:
            if doc.get('date_suppression'):
                doc['date_suppression'] = str(doc['date_suppression'])
        
        return jsonify({"success": True, "documents": documents}), 200
    except Exception as e:
        print(f"[ERREUR] pme_corbeille: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/documents/export", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_export_documents():
    try:
        import csv
        from io import StringIO
        from datetime import datetime
        
        conn = get_db()
        cur = conn.cursor()
        entreprise_id = request.user_entreprise_id
        
        cur.execute("""
            SELECT titre, statut, date_creation, u.nom as auteur
            FROM documents d
            LEFT JOIN users u ON u.id = d.auteur_id
            WHERE d.entreprise_id = %s
            ORDER BY d.date_creation DESC
        """, (entreprise_id,))
        
        docs = cur.fetchall()
        cur.close()
        conn.close()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Titre', 'Statut', 'Date', 'Auteur'])
        for doc in docs:
            writer.writerow([doc['titre'], doc['statut'], doc['date_creation'], doc['auteur']])
        
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mimetype='text/csv')
    except Exception as e:
        print(f"[ERREUR] pme_export_documents: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/document/<int:doc_id>/historique", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_document_historique(doc_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT l.action, l.description, l.date_action, u.nom as utilisateur_nom
            FROM logs l
            LEFT JOIN users u ON u.id = l.user_id
            WHERE l.document_id = %s
            ORDER BY l.date_action DESC
        """, (doc_id,))
        
        historique = cur.fetchall()
        cur.close()
        conn.close()
        
        for h in historique:
            if h.get('date_action'):
                h['date_action'] = str(h['date_action'])
        
        return jsonify({"success": True, "historique": historique}), 200
    except Exception as e:
        print(f"[ERREUR] pme_document_historique: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/workflow/config", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def get_workflow_config():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nom_etape, role_requis, ordre, delai_heures
            FROM workflow_config
            WHERE entreprise_id = %s
            ORDER BY ordre ASC
        """, (request.user_entreprise_id,))
        config = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "config": config}), 200
    except Exception as e:
        print(f"[ERREUR] get_workflow_config: {e}")
        return jsonify({"success": False, "config": []}), 200

@app.route("/api/workflow/config", methods=["POST"])
@token_required
@role_required(['admin_pme'])
def save_workflow_config():
    try:
        data = request.json
        etapes = data.get('etapes', [])
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM workflow_config WHERE entreprise_id = %s", (request.user_entreprise_id,))
        for i, etape in enumerate(etapes):
            cur.execute("""
                INSERT INTO workflow_config (entreprise_id, nom_etape, role_requis, ordre, delai_heures)
                VALUES (%s, %s, %s, %s, %s)
            """, (request.user_entreprise_id, etape['nom'], etape['role'], i + 1, etape.get('delai', 48)))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Workflow enregistré"}), 200
    except Exception as e:
        print(f"[ERREUR] save_workflow_config: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/users/<int:user_id>/reactiver", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def reactiver_user(user_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET actif = 1 WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Utilisateur réactivé"}), 200
    except Exception as e:
        print(f"[ERREUR] reactiver_user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/users/<int:user_id>/reset-password", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def reset_user_password(user_id):
    try:
        data = request.json
        password = data.get('password', 'employe123')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (generate_password_hash(password), user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Mot de passe réinitialisé"}), 200
    except Exception as e:
        print(f"[ERREUR] reset_user_password: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/users/<int:user_id>", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def update_user(user_id):
    try:
        data = request.json
        nom = data.get('nom')
        telephone = data.get('telephone')
        conn = get_db()
        cur = conn.cursor()
        if nom:
            cur.execute("UPDATE users SET nom = %s WHERE id = %s", (nom, user_id))
        if telephone:
            cur.execute("UPDATE users SET telephone = %s WHERE id = %s", (telephone, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Utilisateur modifié"}), 200
    except Exception as e:
        print(f"[ERREUR] update_user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================
# ROUTES PHOTO ET LOGO (simplifiées)
# ============================================

@app.route("/api/user/photo", methods=["GET", "POST"])
@token_required
def user_photo():
    if request.method == "POST":
        file = request.files.get('photo')
        if file:
            filename = f"user_{request.user_id}.jpg"
            upload_dir = os.path.join('static', 'uploads', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            return jsonify({"success": True, "message": "Photo mise à jour"})
        return jsonify({"success": False, "message": "Aucun fichier"}), 400
    else:
        filepath = os.path.join('static', 'uploads', 'profiles', f"user_{request.user_id}.jpg")
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        return '', 204

@app.route("/api/entreprise/logo", methods=["GET", "POST"])
@token_required
def entreprise_logo():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT entreprise_id FROM users WHERE id = %s", (request.user_id,))
    result = cur.fetchone()
    if not result:
        return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
    entreprise_id = result['entreprise_id']
    cur.close()
    conn.close()
    
    if request.method == "POST":
        file = request.files.get('logo')
        if file:
            filename = f"entreprise_{entreprise_id}.jpg"
            upload_dir = os.path.join('static', 'uploads', 'logos')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            return jsonify({"success": True, "message": "Logo mis à jour"})
        return jsonify({"success": False, "message": "Aucun fichier"}), 400
    else:
        filepath = os.path.join('static', 'uploads', 'logos', f"entreprise_{entreprise_id}.jpg")
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        return '', 204


@app.route('/test-pme')
def test_pme():
    return render_template('test-pme.html')
# ==============================
# LANCEMENT DU SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("GED-PME - Serveur demarre")
    print("URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)