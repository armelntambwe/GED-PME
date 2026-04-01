# ============================================
# GED-PME - Application principale
# ============================================

# ==============================
# IMPORTS
# ==============================
import pymysql
from flasgger import Swagger
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from utils.jwt_manager import generer_token
from middleware.auth import token_required, role_required, get_current_user
from utils.logger import ajouter_log
import os
from werkzeug.utils import secure_filename
from utils.file_upload import allowed_file, get_file_size, secure_filename_with_path
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
import mimetypes

# ==============================
# CONNEXION MYSQL
# ==============================

def get_db():
    """Retourne une connexion MySQL"""
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

# Charger la configuration
app.config.from_object(Config)

# Configuration Swagger
app.config['SWAGGER'] = {
    'title': 'GED-PME API',
    'uiversion': 3,
    'description': 'API de gestion électronique de documents adaptée aux PME',
    'version': '1.0.0'
}

swagger = Swagger(app)

print("🔍 Vérification MySQL...")
try:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.close()
    conn.close()
    print("✅ MySQL connecté avec succès")
except Exception as e:
    print(f"❌ Erreur MySQL: {e}")

# ==============================
# ROUTES DE TEST
# ==============================

@app.route("/test-db")
def test_db():
    """Test de connexion à la base de données"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return "Connexion MySQL OK" if result else "Erreur connexion"
    except Exception as e:
        return f"Erreur: {str(e)}"

# ==============================
# AUTHENTIFICATION
# ==============================

@app.route("/register", methods=["POST"])
def register():
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
        
        return jsonify({
            "message": "Utilisateur créé avec succès",
            "user_id": user_id,
            "role": role
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    
    if not data or "email" not in data or "password" not in data:
        return jsonify({
            "success": False,
            "message": "Données manquantes"
        }), 400

    email = data["email"]
    password = data["password"]

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nom, password, role FROM users WHERE email = %s",
            (email,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "Utilisateur non trouvé"
            }), 404

        if not check_password_hash(user['password'], password):
            return jsonify({
                "success": False,
                "message": "Mot de passe incorrect"
            }), 401

        token = generer_token(user['id'], user['role'])

        return jsonify({
            "success": True,
            "message": "Connexion réussie",
            "token": token,
            "user": {
                "id": user['id'],
                "nom": user['nom'],
                "role": user['role']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur serveur: {str(e)}"
        }), 500

@app.route("/profile", methods=["GET"])
@token_required
def profile():
    return jsonify({
        "success": True,
        "user_id": request.user_id,
        "role": request.user_role,
        "message": "Accès autorisé"
    }), 200

# ==============================
# GESTION DES DOCUMENTS
# ==============================

@app.route("/documents", methods=["POST"])
@token_required
def create_document():
    data = request.json
    search = request.args.get("search")  
    if not data or "titre" not in data:
        return jsonify({"success": False, "message": "Titre requis"}), 400
    
    titre = data["titre"]
    description = data.get("description", "")
    auteur_id = request.user_id
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO documents (titre, description, auteur_id, statut)
            VALUES (%s, %s, %s, 'brouillon')
        """, (titre, description, auteur_id))
        
        doc_id = cur.lastrowid
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Document créé avec succès",
            "document_id": doc_id,
            "statut": "brouillon"
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@app.route("/documents", methods=["GET"])
@token_required
def get_documents():
    user_id = request.args.get("user_id")
    statut = request.args.get("statut")
    
    if request.user_role == 'employe':
        if user_id and int(user_id) != request.user_id:
            return jsonify({
                "success": False,
                "message": "Vous ne pouvez voir que vos propres documents"
            }), 403
        if not user_id:
            user_id = str(request.user_id)
    
    conn = get_db()
    cur = conn.cursor()
    
    query = "SELECT id, titre, description, date_creation, statut, auteur_id FROM documents WHERE 1=1"
    params = []
    
    if user_id:
        query += " AND auteur_id = %s"
        params.append(user_id)
    if statut:
        query += " AND statut = %s"
        params.append(statut)
    
    query += " ORDER BY date_creation DESC"
    
    cur.execute(query, params)
    documents = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(documents),
        "documents": documents
    })

@app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
@token_required
def soumettre_document(doc_id):
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT auteur_id, statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            cur.close()
            conn.close()
            return jsonify({"message": "Document non trouvé"}), 404
        
        if doc['auteur_id'] != request.user_id:
            cur.close()
            conn.close()
            return jsonify({"message": "Vous ne pouvez soumettre que vos propres documents"}), 403
        
        if doc['statut'] != 'brouillon':
            cur.close()
            conn.close()
            return jsonify({"message": f"Document déjà soumis (statut: {doc['statut']})"}), 400
        
        cur.execute("UPDATE documents SET statut = 'soumis' WHERE id = %s", (doc_id,))
        conn.commit()
        
        ajouter_log(
            action='SOUMISSION',
            description=f"Document {doc_id} soumis",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Document soumis pour validation"}), 200
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

@app.route("/documents/<int:doc_id>/valider", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def valider_document(doc_id):
    validateur_id = request.user_id
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        
        if doc['statut'] != 'soumis':
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": f"Impossible de valider un document en statut '{doc['statut']}'"}), 400
        
        cur.execute("""
            UPDATE documents 
            SET statut = 'valide', validateur_id = %s, date_validation = NOW() 
            WHERE id = %s AND statut = 'soumis'
        """, (validateur_id, doc_id))
        
        conn.commit()
        
        ajouter_log(
            action='VALIDATION',
            description=f"Document {doc_id} validé",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Document validé avec succès"}), 200
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

@app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def rejeter_document(doc_id):
    data = request.json
    
    if not data or "commentaire" not in data:
        return jsonify({"success": False, "message": "Commentaire requis"}), 400
    
    validateur_id = request.user_id
    commentaire = data["commentaire"]
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Document non trouvé"}), 404
        
        if doc['statut'] != 'soumis':
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": f"Impossible de rejeter un document en statut '{doc['statut']}'"}), 400
        
        cur.execute("""
            UPDATE documents 
            SET statut = 'rejete', validateur_id = %s, commentaire_rejet = %s 
            WHERE id = %s AND statut = 'soumis'
        """, (validateur_id, commentaire, doc_id))
        
        conn.commit()
        
        ajouter_log(
            action='REJET',
            description=f"Document {doc_id} rejeté: {commentaire}",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Document rejeté", "commentaire": commentaire}), 200
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

# ============================================
# UPLOAD ET TÉLÉCHARGEMENT
# ============================================

@app.route("/documents/upload", methods=["POST"])
@token_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier fourni"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Nom de fichier vide"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": f"Format non autorisé"}), 415
    
    file_size = get_file_size(file)
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({"success": False, "message": f"Fichier trop volumineux"}), 413
    
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
            INSERT INTO documents 
            (titre, description, fichier_nom, fichier_chemin, fichier_taille, 
             type_mime, auteur_id, statut, categorie_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'brouillon', %s)
        """, (titre, description, file.filename, filepath, file_size,
              file.mimetype, request.user_id, categorie_id))
        
        doc_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        ajouter_log(
            action='CREATION',
            description=f"Document '{titre}' uploadé",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        return jsonify({
            "success": True,
            "message": "Fichier uploadé avec succès",
            "document": {
                "id": doc_id,
                "titre": titre,
                "fichier_original": file.filename,
                "fichier_stocke": secure_name,
                "taille": file_size,
                "type": file.mimetype,
                "statut": "brouillon"
            }
        }), 201
        
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

@app.route("/documents/<int:doc_id>/download", methods=["GET"])
@token_required
def download_document(doc_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT titre, fichier_chemin, auteur_id 
        FROM documents 
        WHERE id = %s
    """, (doc_id,))
    
    doc = cur.fetchone()
    cur.close()
    conn.close()
    
    if not doc:
        return jsonify({"success": False, "message": "Document non trouvé"}), 404
    
    titre, fichier_chemin, auteur_id = doc['titre'], doc['fichier_chemin'], doc['auteur_id']
    
    if request.user_role == 'employe' and auteur_id != request.user_id:
        return jsonify({"success": False, "message": "Accès non autorisé"}), 403
    
    ajouter_log(
        action='TELECHARGEMENT',
        description=f"Document {doc_id} téléchargé",
        user_id=request.user_id,
        document_id=doc_id
    )
    
    if not os.path.exists(fichier_chemin):
        return jsonify({"success": False, "message": "Fichier introuvable"}), 404
    
    try:
        return send_file(
            fichier_chemin,
            as_attachment=True,
            download_name=titre,
            mimetype=mimetypes.guess_type(fichier_chemin)[0]
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

# ============================================
# GESTION DES CATÉGORIES
# ============================================

@app.route("/categories", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def create_category():
    data = request.json
    
    if not data or "nom" not in data:
        return jsonify({"success": False, "message": "Nom requis"}), 400
    
    nom = data["nom"].strip()
    description = data.get("description", "")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("INSERT INTO categories (nom, description) VALUES (%s, %s)", (nom, description))
        category_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Catégorie créée",
            "category": {"id": category_id, "nom": nom, "description": description}
        }), 201
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

@app.route("/categories", methods=["GET"])
@token_required
def get_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nom, description, date_creation FROM categories ORDER BY nom ASC")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(categories),
        "categories": categories
    })

@app.route("/categories/<int:categorie_id>", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def update_category(categorie_id):
    data = request.json
    
    if not data or ("nom" not in data and "description" not in data):
        return jsonify({"success": False, "message": "Rien à modifier"}), 400
    
    conn = get_db()
    cur = conn.cursor()
    
    updates = []
    params = []
    
    if "nom" in data:
        updates.append("nom = %s")
        params.append(data["nom"])
    if "description" in data:
        updates.append("description = %s")
        params.append(data["description"])
    
    params.append(categorie_id)
    
    try:
        cur.execute(f"UPDATE categories SET {', '.join(updates)} WHERE id = %s", params)
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Catégorie modifiée"}), 200
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

@app.route("/categories/<int:categorie_id>", methods=["DELETE"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def delete_category(categorie_id):
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM categories WHERE id = %s", (categorie_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Catégorie supprimée"}), 200
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

# ============================================
# FICHIERS STATIQUES
# ============================================

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

# ============================================
# ROUTES POUR L'INTERFACE UTILISATEUR
# ============================================

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard-admin')
def dashboard_admin():
    return render_template('dashboard-admin.html')

@app.route('/dashboard-employee')
def dashboard_employee():
    return render_template('dashboard-employee.html')

# ============================================
# ROUTES API POUR TABLEAU DE BORD
# ============================================

@app.route("/api/dashboard/stats", methods=["GET"])
@token_required
def dashboard_stats():
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
# LANCEMENT SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 GED-PME - Serveur démarré")
    print("📝 URL: http://localhost:5000")
    print("📚 Documentation Swagger: http://localhost:5000/apidocs")
    print("=" * 50)
    app.run(debug=True)