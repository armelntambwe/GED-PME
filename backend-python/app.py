# ============================================
# GED-PME - Application principale
# Description : API REST pour la Gestion Électronique de Documents

# ============================================

# ==============================
# IMPORTS DES BIBLIOTHÈQUES
# ==============================

import pymysql
from flasgger import Swagger
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from utils.jwt_manager import generer_token
from middleware.auth import token_required, role_required
from utils.logger import ajouter_log
import os
from werkzeug.utils import secure_filename
from utils.file_upload import allowed_file, get_file_size, secure_filename_with_path
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
import mimetypes
import shutil
from datetime import datetime
import csv
from io import StringIO
import subprocess
from io import BytesIO  

  
# ==============================
# CONNEXION MYSQL
# ==============================

def get_db():
    """Établit la connexion à MySQL et retourne un curseur dict"""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

# ==============================
# INITIALISATION APP
# ==============================

app = Flask(__name__)
app.config.from_object(Config)

app.config['SWAGGER'] = {
    'title': 'GED-PME API',
    'uiversion': 3,
    'description': 'API de gestion électronique de documents adaptée aux PME',
    'version': '2.0'
}
swagger = Swagger(app)

print("🔍 Vérification MySQL...")
try:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.close()
    conn.close()
    print("✅ MySQL connecté")
except Exception as e:
    print(f"❌ Erreur MySQL: {e}")

# ==============================
# ROUTES DE TEST
# ==============================

@app.route("/test-db")
def test_db():
    """Test simple de connexion à MySQL"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return "MySQL OK" if result else "Erreur"
    except Exception as e:
        return f"Erreur: {str(e)}"

# ==============================
# AUTHENTIFICATION
# ==============================

@app.route("/register", methods=["POST"])
def register():
    """Crée un nouvel utilisateur. Body: {nom, email, password, role (optionnel)}"""
    data = request.json
    if not data or "nom" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "Données manquantes"}), 400

    nom = data["nom"]
    email = data["email"]
    role = data.get("role", "employe")
    password = generate_password_hash(data["password"])

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (nom, email, password, role) VALUES (%s, %s, %s, %s)",
            (nom, email, password, role)
        )
        conn.commit()
        user_id = cur.lastrowid
        return jsonify({"message": "Utilisateur créé", "user_id": user_id, "role": role}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    """Authentifie un utilisateur et retourne un token JWT. Body: {email, password}"""
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return jsonify({"success": False, "message": "Données manquantes"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nom, password, role, entreprise_id FROM users WHERE email = %s",
            (data["email"],)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
        if not check_password_hash(user['password'], data["password"]):
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
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500


@app.route("/profile", methods=["GET"])
@token_required
def profile():
    """Retourne les infos de l'utilisateur connecté"""
    return jsonify({"user_id": request.user_id, "role": request.user_role}), 200

# ==============================
# GESTION DES DOCUMENTS
# ==============================

@app.route("/documents", methods=["POST"])
@token_required
def create_document():
    """Crée un document (sans fichier)"""
    data = request.json
    if not data or "titre" not in data:
        return jsonify({"success": False, "message": "Titre requis"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO documents (titre, description, auteur_id, statut)
            VALUES (%s, %s, %s, 'brouillon')
        """, (data["titre"], data.get("description", ""), request.user_id))
        doc_id = cur.lastrowid
        conn.commit()
        return jsonify({"success": True, "document_id": doc_id, "statut": "brouillon"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
@token_required
def soumettre_document(doc_id):
    """Soumet un document pour validation (employé uniquement)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT auteur_id, statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return jsonify({"message": "Document non trouvé"}), 404
        if doc['auteur_id'] != request.user_id:
            return jsonify({"message": "Action non autorisée"}), 403
        if doc['statut'] != 'brouillon':
            return jsonify({"message": f"Statut actuel: {doc['statut']}"}), 400

        cur.execute("UPDATE documents SET statut = 'soumis' WHERE id = %s", (doc_id,))
        conn.commit()
        ajouter_log(action='SOUMISSION', description=f"Document {doc_id} soumis",
                    user_id=request.user_id, document_id=doc_id)
        return jsonify({"success": True, "message": "Document soumis"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/documents/<int:doc_id>/valider", methods=["PUT"])
@token_required
@role_required(['admin_pme'])
def valider_document(doc_id):
    """Valide un document soumis (Admin PME uniquement)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if doc['statut'] != 'soumis':
            return jsonify({"success": False, "message": "Document non soumis"}), 400

        cur.execute("""
            UPDATE documents SET statut = 'valide', validateur_id = %s, date_validation = NOW()
            WHERE id = %s
        """, (request.user_id, doc_id))
        conn.commit()
        ajouter_log(action='VALIDATION', description=f"Document {doc_id} validé",
                    user_id=request.user_id, document_id=doc_id)
        
        # Notification à l'auteur
        envoyer_notification(doc['auteur_id'], 'DOCUMENT_VALIDE', 
                            f"✅ Votre document a été validé", '/dashboard-employee?tab=documents')
        
        return jsonify({"success": True, "message": "Document validé"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
@token_required
@role_required(['admin_pme'])
def rejeter_document(doc_id):
    """Rejette un document avec commentaire (Admin PME uniquement)"""
    data = request.json
    if not data or "commentaire" not in data:
        return jsonify({"success": False, "message": "Commentaire requis"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT statut, auteur_id FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        if doc['statut'] != 'soumis':
            return jsonify({"success": False, "message": "Document non soumis"}), 400

        cur.execute("""
            UPDATE documents SET statut = 'rejete', validateur_id = %s, commentaire_rejet = %s
            WHERE id = %s
        """, (request.user_id, data["commentaire"], doc_id))
        conn.commit()
        ajouter_log(action='REJET', description=f"Document {doc_id} rejeté: {data['commentaire']}",
                    user_id=request.user_id, document_id=doc_id)
        
        # Notification à l'auteur
        envoyer_notification(doc['auteur_id'], 'DOCUMENT_REJETE', 
                            f"❌ Votre document a été rejeté. Motif: {data['commentaire']}", 
                            '/dashboard-employee?tab=documents')
        
        return jsonify({"success": True, "message": "Document rejeté"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ==============================
# UPLOAD ET TÉLÉCHARGEMENT
# ==============================

@app.route("/documents/upload", methods=["POST"])
@token_required
def upload_document():
    """Upload d'un fichier avec ses métadonnées"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nom vide"}), 400
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Format non autorisé"}), 415

    file_size = get_file_size(file)
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({"success": False, "message": "Fichier trop volumineux"}), 413

    try:
        secure_name = secure_filename_with_path(file.filename, request.user_id)
        filepath = os.path.join(UPLOAD_FOLDER, secure_name)
        file.save(filepath)

        titre = request.form.get('titre', file.filename)
        description = request.form.get('description', '')
        categorie_id = request.form.get('categorie_id')

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO documents (titre, description, fichier_nom, fichier_chemin,
             fichier_taille, type_mime, auteur_id, statut, categorie_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'brouillon', %s)
        """, (titre, description, file.filename, filepath, file_size,
              file.mimetype, request.user_id, categorie_id))
        doc_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        ajouter_log(action='CREATION', description=f"Document '{titre}' uploadé",
                    user_id=request.user_id, document_id=doc_id)
        return jsonify({"success": True, "document_id": doc_id}), 201
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/documents/<int:doc_id>/download", methods=["GET"])
@token_required
def download_document(doc_id):
    """Télécharge un fichier (vérifie les droits)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT titre, fichier_chemin, auteur_id FROM documents WHERE id = %s", (doc_id,))
    doc = cur.fetchone()
    cur.close()
    conn.close()

    if not doc:
        return jsonify({"success": False, "message": "Document non trouvé"}), 404
    if request.user_role == 'employe' and doc['auteur_id'] != request.user_id:
        return jsonify({"success": False, "message": "Accès non autorisé"}), 403
    if not os.path.exists(doc['fichier_chemin']):
        return jsonify({"success": False, "message": "Fichier introuvable"}), 404

    ajouter_log(action='TELECHARGEMENT', description=f"Document {doc_id} téléchargé",
                user_id=request.user_id, document_id=doc_id)
    return send_file(doc['fichier_chemin'], as_attachment=True, download_name=doc['titre'])

# ==============================
# GESTION DES CATÉGORIES
# ==============================

@app.route("/categories", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def create_category():
    """Crée une catégorie"""
    data = request.json
    if not data or "nom" not in data:
        return jsonify({"success": False, "message": "Nom requis"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO categories (nom, description) VALUES (%s, %s)",
                    (data["nom"].strip(), data.get("description", "")))
        conn.commit()
        return jsonify({"success": True, "category_id": cur.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/categories", methods=["GET"])
@token_required
def get_categories():
    """Liste toutes les catégories"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nom, description, date_creation FROM categories ORDER BY nom")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"success": True, "categories": categories}), 200


@app.route("/categories/<int:categorie_id>", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def update_category(categorie_id):
    """Modifie une catégorie"""
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Données manquantes"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        if "nom" in data:
            cur.execute("UPDATE categories SET nom = %s WHERE id = %s", (data["nom"], categorie_id))
        if "description" in data:
            cur.execute("UPDATE categories SET description = %s WHERE id = %s", (data["description"], categorie_id))
        conn.commit()
        return jsonify({"success": True, "message": "Catégorie modifiée"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/categories/<int:categorie_id>", methods=["DELETE"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def delete_category(categorie_id):
    """Supprime une catégorie"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM categories WHERE id = %s", (categorie_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Catégorie supprimée"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ==============================
# FICHIERS STATIQUES (PWA)
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

@app.route('/index.html')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/test.html')
def serve_test():
    return send_from_directory('static', 'test.html')

# ==============================
# INTERFACES UTILISATEUR
# ==============================

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard-admin')
def dashboard_admin():
    return render_template('dashboard-admin.html')

@app.route('/dashboard-employee')
def dashboard_employee():
    return render_template('dashboard-employee.html')

@app.route('/dashboard-pme')
def dashboard_pme():
    return render_template('dashboard-admin-pme.html')

@app.route('/dashboard-admin-global')
def dashboard_admin_global():
    return render_template('dashboard-admin-global.html')

# ==============================
# STATISTIQUES (tous rôles)
# ==============================

@app.route("/api/dashboard/stats", methods=["GET"])
@token_required
def dashboard_stats():
    """Statistiques pour tous les dashboards"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM documents")
    total_docs = cur.fetchone()['total']
    cur.execute("SELECT statut, COUNT(*) as count FROM documents GROUP BY statut")
    stats = {row['statut']: row['count'] for row in cur.fetchall()}
    cur.execute("SELECT COUNT(*) as total FROM users")
    total_users = cur.fetchone()['total']
    cur.close()
    conn.close()
    return jsonify({
        "total_documents": total_docs,
        "brouillon": stats.get('brouillon', 0),
        "soumis": stats.get('soumis', 0),
        "valide": stats.get('valide', 0),
        "rejete": stats.get('rejete', 0),
        "total_users": total_users
    })

# ==============================
# GESTION EMPLOYÉS
# ==============================

@app.route("/users", methods=["GET"])
@token_required
def get_users():
    """Liste les employés (admin uniquement)"""
    if request.user_role not in ['admin_global', 'admin_pme']:
        return jsonify({"success": False, "message": "Accès non autorisé"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nom, email, telephone, role, actif, date_inscription
        FROM users
        WHERE role = 'employe'
        ORDER BY id DESC
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    for user in users:
        if user.get('date_inscription'):
            user['date_inscription'] = str(user['date_inscription'])

    return jsonify({"success": True, "count": len(users), "users": users}), 200


@app.route("/users/<int:user_id>/desactiver", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def desactiver_user(user_id):
    """Désactive un compte utilisateur (passe actif à 0)"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

    cur.execute("UPDATE users SET actif = 0 WHERE id = %s", (user_id,))
    conn.commit()

    ajouter_log(action='DESACTIVATION_USER',
                description=f"Utilisateur {user_id} désactivé",
                user_id=request.user_id)

    cur.close()
    conn.close()

    return jsonify({"success": True, "message": "Utilisateur désactivé"}), 200


@app.route("/admin/employes", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def create_employe():
    """Crée un employé"""
    data = request.json
    if not data or "nom" not in data or "email" not in data:
        return jsonify({"success": False, "message": "Nom et email requis"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (data["email"],))
    if cur.fetchone():
        return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

    try:
        cur.execute("""
            INSERT INTO users (nom, email, password, telephone, role, actif, entreprise_id)
            VALUES (%s, %s, %s, %s, 'employe', 1, %s)
        """, (data["nom"], data["email"], generate_password_hash(data.get("password", "employe123")),
              data.get("telephone", ""), request.user_entreprise_id))
        user_id = cur.lastrowid
        conn.commit()
        ajouter_log(action='CREATION_EMPLOYE', description=f"Employé {data['nom']} créé",
                    user_id=request.user_id)
        
        # Notification à l'admin PME
        envoyer_notification(request.user_id, 'EMPLOYE_CREE', 
                            f"👤 L'employé {data['nom']} a été créé", 
                            '/dashboard-pme?tab=employes')
        
        return jsonify({"success": True, "user_id": user_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ==============================
# ROUTES ADMIN GLOBAL
# ==============================

@app.route("/api/admin-global/stats", methods=["GET"])
@token_required
@role_required(['admin_global'])
def admin_global_stats():
    """Statistiques globales (Admin Global)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM entreprises")
    total_entreprises = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM documents")
    total_documents = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM users WHERE actif = 1")
    total_users = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM documents WHERE statut = 'soumis'")
    en_attente = cur.fetchone()['total']
    cur.close()
    conn.close()
    return jsonify({
        "success": True,
        "stats": {
            "total_entreprises": total_entreprises,
            "total_documents": total_documents,
            "total_users": total_users,
            "docs_en_attente": en_attente
        }
    }), 200


@app.route("/api/admin-global/entreprises", methods=["GET"])
@token_required
@role_required(['admin_global'])
def get_all_entreprises():
    """Liste toutes les entreprises (sans le statut pour le tableau)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.nom, e.adresse, e.telephone, e.email,
               COUNT(DISTINCT u.id) AS nb_employes,
               COUNT(DISTINCT d.id) AS nb_documents
        FROM entreprises e
        LEFT JOIN users u ON u.entreprise_id = e.id
        LEFT JOIN documents d ON d.entreprise_id = e.id
        GROUP BY e.id
        ORDER BY e.nom ASC
    """)
    entreprises = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"success": True, "entreprises": entreprises}), 200


@app.route("/api/admin-global/entreprises", methods=["POST"])
@token_required
@role_required(['admin_global'])
def create_entreprise():
    """Crée une nouvelle entreprise"""
    data = request.json
    if not data or not data.get('nom'):
        return jsonify({"success": False, "message": "Nom requis"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO entreprises (nom, adresse, telephone, email)
            VALUES (%s, %s, %s, %s)
        """, (data['nom'], data.get('adresse', ''), data.get('telephone', ''), data.get('email', '')))
        entreprise_id = cur.lastrowid
        conn.commit()
        
        # Notification à l'admin global
        envoyer_notification(request.user_id, 'ENTREPRISE_CREEE', 
                            f"✅ L'entreprise {data['nom']} a été créée", 
                            '/dashboard-admin-global?tab=entreprises')
        
        return jsonify({"success": True, "entreprise_id": entreprise_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/admin-global/entreprises/<int:entreprise_id>", methods=["PUT"])
@token_required
@role_required(['admin_global'])
def update_entreprise(entreprise_id):
    """Modifie une entreprise"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nom FROM entreprises WHERE id = %s", (entreprise_id,))
    ent = cur.fetchone()
    if not ent:
        return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

    updates = []
    params = []
    if 'nom' in data:
        updates.append("nom = %s")
        params.append(data['nom'])
    if 'adresse' in data:
        updates.append("adresse = %s")
        params.append(data['adresse'])
    if 'telephone' in data:
        updates.append("telephone = %s")
        params.append(data['telephone'])
    if 'email' in data:
        updates.append("email = %s")
        params.append(data['email'])

    if not updates:
        return jsonify({"success": False, "message": "Rien à modifier"}), 400

    params.append(entreprise_id)
    cur.execute(f"UPDATE entreprises SET {', '.join(updates)} WHERE id = %s", params)
    conn.commit()
    cur.close()
    conn.close()
    
    # Notification
    envoyer_notification(request.user_id, 'ENTREPRISE_MODIFIEE', 
                        f"📝 L'entreprise {ent['nom']} a été modifiée", 
                        '/dashboard-admin-global?tab=entreprises')
    
    return jsonify({"success": True, "message": "Entreprise modifiée"}), 200


@app.route("/api/admin-global/entreprises/<int:entreprise_id>/toggle", methods=["PUT"])
@token_required
@role_required(['admin_global'])
def toggle_entreprise(entreprise_id):
    """Active ou suspend une entreprise"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT statut, nom FROM entreprises WHERE id = %s", (entreprise_id,))
    ent = cur.fetchone()
    if not ent:
        return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

    nouvel_etat = 'suspendu' if ent['statut'] == 'actif' else 'actif'
    cur.execute("UPDATE entreprises SET statut = %s WHERE id = %s", (nouvel_etat, entreprise_id))
    conn.commit()
    cur.close()
    conn.close()
    
    # Notification
    envoyer_notification(request.user_id, 'ENTREPRISE_TOGGLE', 
                        f"🔄 L'entreprise {ent['nom']} est maintenant {nouvel_etat}", 
                        '/dashboard-admin-global?tab=entreprises')
    
    return jsonify({"success": True, "statut": nouvel_etat}), 200


@app.route("/api/admin-global/documents/recents", methods=["GET"])
@token_required
@role_required(['admin_global'])
def get_all_documents_recent():
    """Derniers 50 documents (toutes entreprises)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.titre, d.statut, d.date_creation,
               u.nom AS auteur, e.nom AS entreprise
        FROM documents d
        LEFT JOIN users u ON u.id = d.auteur_id
        LEFT JOIN entreprises e ON e.id = d.entreprise_id
        ORDER BY d.date_creation DESC LIMIT 50
    """)
    docs = cur.fetchall()
    cur.close()
    conn.close()
    for doc in docs:
        if doc.get('date_creation'):
            doc['date_creation'] = str(doc['date_creation'])
    return jsonify({"success": True, "documents": docs}), 200



@app.route("/api/admin-global/stats/evolution", methods=["GET"])
@token_required
@role_required(['admin_global'])
def stats_evolution():
    """Évolution des documents (8 semaines)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(date_creation, '%Y-%m-%d') as date_jour, COUNT(*) as total
        FROM documents
        WHERE date_creation >= DATE_SUB(NOW(), INTERVAL 8 WEEK)
        GROUP BY DATE(date_creation) ORDER BY date_jour ASC
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({
        "success": True,
        "labels": [r['date_jour'] for r in results],
        "data": [r['total'] for r in results]
    }), 200


@app.route("/api/admin-global/storage", methods=["GET"])
@token_required
@role_required(['admin_global'])
def get_storage_info():
    """Espace disque utilisé"""
    total, used, free = shutil.disk_usage(UPLOAD_FOLDER)
    total_upload = 0
    for dirpath, _, filenames in os.walk(UPLOAD_FOLDER):
        for f in filenames:
            total_upload += os.path.getsize(os.path.join(dirpath, f))
    return jsonify({
        "success": True,
        "storage": {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "uploads_mb": round(total_upload / (1024**2), 2)
        }
    }), 200


@app.route("/api/admin-global/logs/export", methods=["GET"])
@token_required
@role_required(['admin_global'])
def export_logs_csv():
    """Exporte les logs en CSV"""
    import tempfile
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.date_action, l.action, l.description, u.nom as utilisateur, e.nom as entreprise
            FROM logs l
            LEFT JOIN users u ON u.id = l.user_id
            LEFT JOIN entreprises e ON e.id = u.entreprise_id
            ORDER BY l.date_action DESC
        """)
        logs = cur.fetchall()
        cur.close()
        conn.close()

        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Date;Action;Description;Utilisateur;Entreprise\n")
            for log in logs:
                f.write(f"{log.get('date_action', '')};{log.get('action', '')};{log.get('description', '')};{log.get('utilisateur', '')};{log.get('entreprise', '')}\n")
            temp_path = f.name
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"[ERREUR] Export logs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin-global/backup", methods=["POST"])
@token_required
@role_required(['admin_global'])
def manual_backup():
    """Sauvegarde manuelle"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backups/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    try:
        subprocess.run(['mysqldump', '-u', Config.MYSQL_USER, f'-p{Config.MYSQL_PASSWORD}',
                        Config.MYSQL_DB, '--result-file', f"{backup_dir}/database.sql"], check=True)
        shutil.copytree(UPLOAD_FOLDER, f"{backup_dir}/uploads")
        ajouter_log(action='BACKUP_MANUEL', description=f"Sauvegarde {timestamp}", user_id=request.user_id)
        
        envoyer_notification(request.user_id, 'BACKUP_EFFECTUE', 
                            f"💾 Sauvegarde manuelle effectuée à {timestamp}", 
                            '/dashboard-admin-global?tab=storage')
        
        return jsonify({"success": True, "backup_path": backup_dir}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin-global/all-users", methods=["GET"])
@token_required
@role_required(['admin_global'])
def get_all_users():
    """Liste tous les utilisateurs (Admin Global)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT u.id, u.nom, u.email, u.telephone, u.role, u.actif, u.date_inscription,
                   e.nom as entreprise_nom
            FROM users u 
            LEFT JOIN entreprises e ON e.id = u.entreprise_id
            ORDER BY u.id DESC
        """)
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        for user in users:
            if user.get('date_inscription'):
                user['date_inscription'] = str(user['date_inscription'])
        
        return jsonify({"success": True, "users": users}), 200
        
    except Exception as e:
        cur.close()
        conn.close()
        print(f"[ERREUR] get_all_users: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin-global/all-documents", methods=["GET"])
@token_required
@role_required(['admin_global'])
def get_all_documents_admin():
    """Liste tous les documents (Admin Global)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.titre, d.statut, d.date_creation,
               u.nom as auteur_nom, e.nom as entreprise_nom
        FROM documents d
        LEFT JOIN users u ON u.id = d.auteur_id
        LEFT JOIN entreprises e ON e.id = d.entreprise_id
        ORDER BY d.date_creation DESC LIMIT 100
    """)
    docs = cur.fetchall()
    cur.close()
    conn.close()
    for doc in docs:
        if doc.get('date_creation'):
            doc['date_creation'] = str(doc['date_creation'])
    return jsonify({"success": True, "documents": docs}), 200


@app.route("/api/admin-global/all-logs", methods=["GET"])
@token_required
@role_required(['admin_global'])
def get_all_logs_admin():
    """Liste tous les logs (Admin Global)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.id, l.action, l.description, l.date_action, l.date,
                   u.nom as utilisateur_nom, u.role
            FROM logs l 
            LEFT JOIN users u ON u.id = l.user_id
            ORDER BY l.date_action DESC 
            LIMIT 200
        """)
        logs = cur.fetchall()
        cur.close()
        conn.close()
        
        for log in logs:
            if log.get('date_action'):
                log['date_action'] = str(log['date_action'])
            if log.get('date'):
                log['date'] = str(log['date'])
        
        return jsonify({"success": True, "logs": logs}), 200
        
    except Exception as e:
        cur.close()
        conn.close()
        print(f"[ERREUR] get_all_logs_admin: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ==============================
# NOTIFICATIONS
# ==============================

def envoyer_notification(user_id, type_notif, message, lien=None):
    """Envoie une notification à un utilisateur"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notifications (user_id, type, message, lien)
        VALUES (%s, %s, %s, %s)
    """, (user_id, type_notif, message, lien))
    conn.commit()
    cur.close()
    conn.close()


@app.route("/notifications", methods=["GET"])
@token_required
def get_notifications():
    """Récupère les notifications non lues de l'utilisateur"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, message, lien, date_creation
        FROM notifications
        WHERE user_id = %s AND lue = 0
        ORDER BY date_creation DESC
        LIMIT 50
    """, (request.user_id,))
    notifs = cur.fetchall()
    cur.close()
    conn.close()
    
    for notif in notifs:
        if notif.get('date_creation'):
            notif['date_creation'] = str(notif['date_creation'])
    
    return jsonify({"success": True, "notifications": notifs}), 200


@app.route("/notifications/<int:notif_id>/lire", methods=["PUT"])
@token_required
def lire_notification(notif_id):
    """Marque une notification comme lue"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE notifications SET lue = 1 WHERE id = %s AND user_id = %s", 
                (notif_id, request.user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True}), 200


@app.route("/notifications/lire-tout", methods=["PUT"])
@token_required
def lire_toutes_notifications():
    """Marque toutes les notifications comme lues"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE notifications SET lue = 1 WHERE user_id = %s", (request.user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True}), 200


@app.route("/notifications/count", methods=["GET"])
@token_required
def count_notifications():
    """Compte les notifications non lues"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM notifications WHERE user_id = %s AND lue = 0", 
                (request.user_id,))
    count = cur.fetchone()['total']
    cur.close()
    conn.close()
    return jsonify({"success": True, "count": count}), 200

@app.route("/notifications/all", methods=["GET"])
@token_required
def get_all_notifications():
    """Récupère toutes les notifications (lues et non lues)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, message, lien, date_creation, lue
        FROM notifications
        WHERE user_id = %s
        ORDER BY date_creation DESC
        LIMIT 100
    """, (request.user_id,))
    notifs = cur.fetchall()
    cur.close()
    conn.close()
    
    for notif in notifs:
        if notif.get('date_creation'):
            notif['date_creation'] = str(notif['date_creation'])
    
    return jsonify({"success": True, "notifications": notifs}), 200

# ==============================
# LANCEMENT DU SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 GED-PME - Serveur démarré")
    print("📝 URL: http://localhost:5000")
    print("📚 Documentation: http://localhost:5000/apidocs")
    print("=" * 50)
    app.run(debug=True)