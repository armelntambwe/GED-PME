# ============================================
# GED-PME - Application principale
# Conception et déploiement d'une GED adaptée aux PME locales en RDC
# ============================================

# ==============================
# IMPORTS
# ==============================
from flasgger import Swagger
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from utils.jwt_manager import generer_token
from middleware.auth import token_required, role_required, get_current_user
from utils.logger import ajouter_log
import os
from werkzeug.utils import secure_filename
from utils.file_upload import allowed_file, get_file_size, secure_filename_with_path
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS
import mimetypes

# ==============================
# INITIALISATION APP
# ==============================

app = Flask(__name__)

# Configuration Swagger
app.config['SWAGGER'] = {
    'title': 'GED-PME API',
    'uiversion': 3,
    'description': 'API de gestion électronique de documents adaptée aux PME',
    'version': '1.0.0'
}

swagger = Swagger(app)
app.config.from_object(Config)
mysql = MySQL(app)

# ==============================
# ROUTES DE TEST
# ==============================

@app.route("/")
def home():
    """Route principale de test"""
    return "GED-PME connecté à MySQL"

@app.route("/test-db")
def test_db():
    """Test de connexion à la base de données"""
    cur = mysql.connection.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    cur.close()
    return "Connexion MySQL OK" if result else "Erreur connexion"

# ==============================
# AUTHENTIFICATION
# ==============================

@app.route("/register", methods=["POST"])
def register():
    """
    Inscription utilisateur
    ---
    tags:
      - Authentification
    summary: Crée un nouveau compte utilisateur
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: Jean Dupont
            email:
              type: string
              example: jean@test.com
            password:
              type: string
              example: password123
            role:
              type: string
              enum: ['admin_global', 'admin_pme', 'employe']
              default: 'employe'
    responses:
      201:
        description: Utilisateur créé avec succès
      400:
        description: Données manquantes
      500:
        description: Erreur serveur
    """
    data = request.json
    
    if not data or "nom" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "Données manquantes"}), 400
    
    nom = data["nom"]
    email = data["email"]
    role = data.get("role", "employe")
    password = generate_password_hash(data["password"])
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute(
            "INSERT INTO users (nom, email, password, role) VALUES (%s, %s, %s, %s)",
            (nom, email, password, role)
        )
        mysql.connection.commit()
        user_id = cur.lastrowid
        
        return jsonify({
            "message": "Utilisateur créé avec succès",
            "user_id": user_id,
            "role": role
        }), 201
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()

@app.route("/login", methods=["POST"])
def login():
    """
    Authentification utilisateur
    ---
    tags:
      - Authentification
    summary: Connecte un utilisateur et retourne un token JWT
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: admin@test.com
            password:
              type: string
              example: admin123
    responses:
      200:
        description: Connexion réussie
        schema:
          type: object
          properties:
            success:
              type: boolean
            token:
              type: string
            user:
              type: object
      400:
        description: Données manquantes
      401:
        description: Mot de passe incorrect
      404:
        description: Utilisateur non trouvé
    """
    data = request.json
    
    if not data or "email" not in data or "password" not in data:
        return jsonify({
            "success": False,
            "message": "Données manquantes"
        }), 400

    email = data["email"]
    password = data["password"]

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id, nom, password, role FROM users WHERE email = %s",
            (email,)
        )
        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "Utilisateur non trouvé"
            }), 404

        if not check_password_hash(user[2], password):
            return jsonify({
                "success": False,
                "message": "Mot de passe incorrect"
            }), 401

        token = generer_token(user[0], user[3])

        return jsonify({
            "success": True,
            "message": "Connexion réussie",
            "token": token,
            "user": {
                "id": user[0],
                "nom": user[1],
                "role": user[3]
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
    """
    Profil utilisateur
    ---
    tags:
      - Authentification
    summary: Retourne les informations de l'utilisateur connecté
    security:
      - Bearer: []
    responses:
      200:
        description: Informations utilisateur
      401:
        description: Non authentifié
    """
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
    """
    Créer un document (métadonnées)
    ---
    tags:
      - Documents
    summary: Crée un nouveau document en statut brouillon
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            titre:
              type: string
              example: Facture Décembre
            description:
              type: string
              example: Facture fournisseur
    responses:
      201:
        description: Document créé
      400:
        description: Titre requis
      500:
        description: Erreur serveur
    """
    data = request.json
    
    if not data or "titre" not in data:
        return jsonify({
            "success": False,
            "message": "Titre requis"
        }), 400
    
    titre = data["titre"]
    description = data.get("description", "")
    auteur_id = request.user_id
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            INSERT INTO documents (titre, description, auteur_id, statut)
            VALUES (%s, %s, %s, 'brouillon')
        """, (titre, description, auteur_id))
        
        doc_id = cur.lastrowid
        mysql.connection.commit()
        
        return jsonify({
            "success": True,
            "message": "Document créé avec succès",
            "document_id": doc_id,
            "statut": "brouillon"
        }), 201
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500
    finally:
        cur.close()

@app.route("/documents", methods=["GET"])
@token_required
def get_documents():
    """
    Lister les documents
    ---
    tags:
      - Documents
    summary: Récupère la liste des documents avec filtres
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Filtrer par utilisateur
      - name: statut
        in: query
        type: string
        required: false
        enum: ['brouillon', 'soumis', 'valide', 'rejete', 'archive']
        description: Filtrer par statut
    responses:
      200:
        description: Liste des documents
      403:
        description: Accès non autorisé
    """
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
    
    cur = mysql.connection.cursor()
    
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
    
    result = []
    for doc in documents:
        result.append({
            "id": doc[0],
            "titre": doc[1],
            "description": doc[2],
            "date_creation": str(doc[3]),
            "statut": doc[4],
            "auteur_id": doc[5]
        })
    
    return jsonify({
        "success": True,
        "count": len(result),
        "documents": result
    })

@app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
@token_required
def soumettre_document(doc_id):
    """
    Soumettre un document
    ---
    tags:
      - Documents
    summary: Soumet un document pour validation
    security:
      - Bearer: []
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Document soumis
      403:
        description: Non autorisé
      404:
        description: Document non trouvé
    """
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("SELECT auteur_id, statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            cur.close()
            return jsonify({"message": "Document non trouvé"}), 404
        
        if doc[0] != request.user_id:
            cur.close()
            return jsonify({"message": "Vous ne pouvez soumettre que vos propres documents"}), 403
        
        if doc[1] != 'brouillon':
            cur.close()
            return jsonify({"message": f"Document déjà soumis (statut: {doc[1]})"}), 400
        
        cur.execute("SELECT entreprise_id FROM users WHERE id = %s", (request.user_id,))
        user_entreprise = cur.fetchone()
        
        if not user_entreprise or not user_entreprise[0]:
            cur.execute("UPDATE documents SET statut = 'soumis' WHERE id = %s", (doc_id,))
            mysql.connection.commit()
            cur.close()
            
            ajouter_log(
                action='SOUMISSION',
                description=f"Document {doc_id} soumis",
                user_id=request.user_id,
                document_id=doc_id
            )
            
            return jsonify({"message": "Document soumis pour validation"}), 200
        
        entreprise_id = user_entreprise[0]
        
        cur.execute("""
            SELECT id FROM niveaux_validation 
            WHERE entreprise_id = %s
            ORDER BY ordre ASC LIMIT 1
        """, (entreprise_id,))
        
        premiere_etape = cur.fetchone()
        
        if premiere_etape:
            niveau_id = premiere_etape[0]
            
            cur.execute("""
                INSERT INTO validations_document (document_id, niveau_id)
                VALUES (%s, %s)
            """, (doc_id, niveau_id))
            
            cur.execute("""
                UPDATE documents 
                SET statut = 'soumis', niveau_validation_actuel = 1 
                WHERE id = %s
            """, (doc_id,))
            
            cur.execute("SELECT COUNT(*) FROM niveaux_validation WHERE entreprise_id = %s", (entreprise_id,))
            total_etapes = cur.fetchone()[0]
            
            message = f"Document soumis - Étape 1/{total_etapes}"
        else:
            cur.execute("UPDATE documents SET statut = 'soumis' WHERE id = %s", (doc_id,))
            message = "Document soumis pour validation"
        
        mysql.connection.commit()
        
        ajouter_log(
            action='SOUMISSION',
            description=f"Document {doc_id} soumis",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        cur.close()
        return jsonify({
            "success": True,
            "message": message
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@app.route("/documents/<int:doc_id>/valider", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def valider_document(doc_id):
    """
    Valider un document
    ---
    tags:
      - Documents
    summary: Valide un document soumis (admin seulement)
    security:
      - Bearer: []
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Document validé
      403:
        description: Non autorisé
      404:
        description: Document non trouvé
    """
    validateur_id = request.user_id
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("SELECT statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            cur.close()
            return jsonify({
                "success": False,
                "message": "Document non trouvé"
            }), 404
        
        if doc[0] != 'soumis':
            cur.close()
            return jsonify({
                "success": False,
                "message": f"Impossible de valider un document en statut '{doc[0]}'"
            }), 400
        
        cur.execute("""
            UPDATE documents 
            SET statut = 'valide', 
                validateur_id = %s, 
                date_validation = NOW() 
            WHERE id = %s AND statut = 'soumis'
        """, (validateur_id, doc_id))
        
        mysql.connection.commit()
        
        ajouter_log(
            action='VALIDATION',
            description=f"Document {doc_id} validé",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        if cur.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Document non trouvé ou déjà traité"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Document validé avec succès"
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500
    finally:
        cur.close()

@app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def rejeter_document(doc_id):
    """
    Rejeter un document
    ---
    tags:
      - Documents
    summary: Rejette un document soumis avec commentaire (admin seulement)
    security:
      - Bearer: []
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            commentaire:
              type: string
              example: Document incomplet
    responses:
      200:
        description: Document rejeté
      400:
        description: Commentaire requis
      403:
        description: Non autorisé
      404:
        description: Document non trouvé
    """
    data = request.json
    
    if not data or "commentaire" not in data:
        return jsonify({
            "success": False,
            "message": "Commentaire requis pour expliquer le rejet"
        }), 400
    
    validateur_id = request.user_id
    commentaire = data["commentaire"]
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("SELECT statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            cur.close()
            return jsonify({
                "success": False,
                "message": "Document non trouvé"
            }), 404
        
        if doc[0] != 'soumis':
            cur.close()
            return jsonify({
                "success": False,
                "message": f"Impossible de rejeter un document en statut '{doc[0]}'"
            }), 400
        
        cur.execute("""
            UPDATE documents 
            SET statut = 'rejete', 
                validateur_id = %s, 
                commentaire_rejet = %s 
            WHERE id = %s AND statut = 'soumis'
        """, (validateur_id, commentaire, doc_id))
        
        mysql.connection.commit()
        
        ajouter_log(
            action='REJET',
            description=f"Document {doc_id} rejeté: {commentaire}",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        if cur.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Document non trouvé ou déjà traité"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Document rejeté",
            "commentaire": commentaire
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500
    finally:
        cur.close()

# ============================================
# UPLOAD ET TÉLÉCHARGEMENT DE FICHIERS
# ============================================

@app.route("/documents/upload", methods=["POST"])
@token_required
def upload_document():
    """
    Uploader un fichier
    ---
    tags:
      - Documents
    summary: Upload un fichier avec ses métadonnées
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Le fichier à uploader
      - name: titre
        in: formData
        type: string
        required: false
        description: Titre du document
      - name: description
        in: formData
        type: string
        required: false
        description: Description du document
      - name: categorie_id
        in: formData
        type: integer
        required: false
        description: ID de la catégorie
    responses:
      201:
        description: Fichier uploadé avec succès
      400:
        description: Erreur de validation
      413:
        description: Fichier trop volumineux
      415:
        description: Format non supporté
    """
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "message": "Aucun fichier fourni. Champ 'file' requis."
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            "success": False,
            "message": "Nom de fichier vide."
        }), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": f"Format non autorisé. Formats acceptés: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 415
    
    file_size = get_file_size(file)
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({
            "success": False,
            "message": f"Fichier trop volumineux. Taille max: {MAX_CONTENT_LENGTH/1024/1024:.0f} Mo"
        }), 413
    
    try:
        secure_name = secure_filename_with_path(file.filename, request.user_id)
        filepath = os.path.join(UPLOAD_FOLDER, secure_name)
        file.save(filepath)
        
        titre = request.form.get('titre', file.filename)
        description = request.form.get('description', '')
        categorie_id = request.form.get('categorie_id')
        
        cur = mysql.connection.cursor()
        
        cur.execute("""
            INSERT INTO documents 
            (titre, description, fichier_nom, fichier_chemin, fichier_taille, 
             type_mime, auteur_id, statut, categorie_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'brouillon', %s)
        """, (
            titre, description, file.filename, filepath, file_size,
            file.mimetype, request.user_id, categorie_id
        ))
        
        doc_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        
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
        return jsonify({
            "success": False,
            "message": f"Erreur lors de l'upload: {str(e)}"
        }), 500

@app.route("/documents/<int:doc_id>/download", methods=["GET"])
@token_required
def download_document(doc_id):
    """
    Télécharger un fichier
    ---
    tags:
      - Documents
    summary: Télécharge le fichier d'un document
    security:
      - Bearer: []
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Fichier téléchargé
      403:
        description: Accès non autorisé
      404:
        description: Document ou fichier non trouvé
    """
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT titre, fichier_chemin, auteur_id 
        FROM documents 
        WHERE id = %s
    """, (doc_id,))
    
    doc = cur.fetchone()
    cur.close()
    
    if not doc:
        return jsonify({
            "success": False,
            "message": "Document non trouvé"
        }), 404
    
    titre, fichier_chemin, auteur_id = doc
    
    if request.user_role == 'employe' and auteur_id != request.user_id:
        return jsonify({
            "success": False,
            "message": "Vous n'avez pas le droit de télécharger ce document"
        }), 403
    
    ajouter_log(
        action='TELECHARGEMENT',
        description=f"Document {doc_id} téléchargé",
        user_id=request.user_id,
        document_id=doc_id
    )
    
    if not os.path.exists(fichier_chemin):
        return jsonify({
            "success": False,
            "message": "Fichier introuvable sur le serveur"
        }), 404
    
    try:
        return send_file(
            fichier_chemin,
            as_attachment=True,
            download_name=titre,
            mimetype=mimetypes.guess_type(fichier_chemin)[0]
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors du téléchargement: {str(e)}"
        }), 500

# ============================================
# GESTION DES CATÉGORIES
# ============================================

@app.route("/categories", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def create_category():
    """
    Créer une catégorie
    ---
    tags:
      - Catégories
    summary: Crée une nouvelle catégorie (admin seulement)
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: Factures
            description:
              type: string
              example: Documents comptables
    responses:
      201:
        description: Catégorie créée
      400:
        description: Nom requis
      409:
        description: Catégorie déjà existante
    """
    data = request.json
    
    if not data or "nom" not in data:
        return jsonify({
            "success": False,
            "message": "Le nom de la catégorie est requis"
        }), 400
    
    nom = data["nom"].strip()
    description = data.get("description", "")
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE nom = %s", (nom,))
    existing = cur.fetchone()
    
    if existing:
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Une catégorie '{nom}' existe déjà"
        }), 409
    
    try:
        cur.execute("""
            INSERT INTO categories (nom, description)
            VALUES (%s, %s)
        """, (nom, description))
        
        category_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "success": True,
            "message": "Catégorie créée avec succès",
            "category": {
                "id": category_id,
                "nom": nom,
                "description": description
            }
        }), 201
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@app.route("/categories", methods=["GET"])
@token_required
def get_categories():
    """
    Lister les catégories
    ---
    tags:
      - Catégories
    summary: Retourne la liste de toutes les catégories
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des catégories
    """
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, nom, description, date_creation 
        FROM categories 
        ORDER BY nom ASC
    """)
    
    categories = cur.fetchall()
    cur.close()
    
    result = []
    for cat in categories:
        result.append({
            "id": cat[0],
            "nom": cat[1],
            "description": cat[2],
            "date_creation": str(cat[3])
        })
    
    return jsonify({
        "success": True,
        "count": len(result),
        "categories": result
    }), 200

@app.route("/categories/<int:categorie_id>", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def update_category(categorie_id):
    """
    Modifier une catégorie
    ---
    tags:
      - Catégories
    summary: Modifie une catégorie existante (admin seulement)
    security:
      - Bearer: []
    parameters:
      - name: categorie_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: Nouvelles Factures
            description:
              type: string
              example: Nouvelle description
    responses:
      200:
        description: Catégorie modifiée
      404:
        description: Catégorie non trouvée
      409:
        description: Nom déjà utilisé
    """
    data = request.json
    
    if not data or ("nom" not in data and "description" not in data):
        return jsonify({
            "success": False,
            "message": "Rien à modifier. Fournissez 'nom' ou 'description'."
        }), 400
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nom, description FROM categories WHERE id = %s", (categorie_id,))
    category = cur.fetchone()
    
    if not category:
        cur.close()
        return jsonify({
            "success": False,
            "message": "Catégorie non trouvée"
        }), 404
    
    if "nom" in data and data["nom"] != category[1]:
        cur.execute("SELECT id FROM categories WHERE nom = %s AND id != %s", 
                   (data["nom"], categorie_id))
        existing = cur.fetchone()
        
        if existing:
            cur.close()
            return jsonify({
                "success": False,
                "message": f"Une catégorie '{data['nom']}' existe déjà"
            }), 409
    
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
        query = f"UPDATE categories SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        mysql.connection.commit()
        
        cur.execute("SELECT id, nom, description, date_creation FROM categories WHERE id = %s", 
                   (categorie_id,))
        updated = cur.fetchone()
        cur.close()
        
        return jsonify({
            "success": True,
            "message": "Catégorie modifiée avec succès",
            "category": {
                "id": updated[0],
                "nom": updated[1],
                "description": updated[2],
                "date_creation": str(updated[3])
            }
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@app.route("/categories/<int:categorie_id>", methods=["DELETE"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def delete_category(categorie_id):
    """
    Supprimer une catégorie
    ---
    tags:
      - Catégories
    summary: Supprime une catégorie (admin seulement)
    security:
      - Bearer: []
    parameters:
      - name: categorie_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Catégorie supprimée
      404:
        description: Catégorie non trouvée
    """
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nom FROM categories WHERE id = %s", (categorie_id,))
    category = cur.fetchone()
    
    if not category:
        cur.close()
        return jsonify({
            "success": False,
            "message": "Catégorie non trouvée"
        }), 404
    
    cur.execute("SELECT COUNT(*) FROM documents WHERE categorie_id = %s", (categorie_id,))
    count = cur.fetchone()[0]
    
    try:
        cur.execute("DELETE FROM categories WHERE id = %s", (categorie_id,))
        mysql.connection.commit()
        cur.close()
        
        message = f"Catégorie '{category[1]}' supprimée"
        if count > 0:
            message += f". {count} document(s) n'ont plus de catégorie."
        
        return jsonify({
            "success": True,
            "message": message
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

# ============================================
# WORKFLOW ET VALIDATIONS
# ============================================

@app.route("/entreprise/workflow", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def configurer_workflow():
    """
    Configurer le workflow
    ---
    tags:
      - Workflow
    summary: Configure les étapes de validation pour une entreprise (admin)
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            etapes:
              type: array
              items:
                type: object
                properties:
                  nom:
                    type: string
                    example: Chef d'équipe
                  role:
                    type: string
                    enum: ['admin_global', 'admin_pme', 'manager', 'employe']
                  delai:
                    type: integer
                    example: 24
    responses:
      200:
        description: Workflow configuré
      400:
        description: Erreur de paramètres
    """
    cur = mysql.connection.cursor()
    cur.execute("SELECT entreprise_id FROM users WHERE id = %s", (request.user_id,))
    result = cur.fetchone()
    
    if not result or not result[0]:
        cur.close()
        return jsonify({
            "success": False,
            "message": "Vous n'êtes pas associé à une entreprise"
        }), 400
    
    entreprise_id = result[0]
    data = request.json
    
    if not data or "etapes" not in data:
        return jsonify({
            "success": False,
            "message": "La liste des étapes est requise"
        }), 400
    
    etapes = data["etapes"]
    
    if not isinstance(etapes, list) or len(etapes) == 0:
        return jsonify({
            "success": False,
            "message": "Au moins une étape est requise"
        }), 400
    
    try:
        cur.execute("DELETE FROM niveaux_validation WHERE entreprise_id = %s", (entreprise_id,))
        
        for i, etape in enumerate(etapes, 1):
            if etape["role"] not in ['admin_global', 'admin_pme', 'manager', 'employe']:
                continue
            
            delai = etape.get("delai", 48)
            
            cur.execute("""
                INSERT INTO niveaux_validation 
                (entreprise_id, nom_niveau, ordre, role_requis, delai_heures)
                VALUES (%s, %s, %s, %s, %s)
            """, (entreprise_id, etape["nom"], i, etape["role"], delai))
        
        mysql.connection.commit()
        cur.close()
        
        ajouter_log(
            action='CONFIG_WORKFLOW',
            description=f"Workflow configuré avec {len(etapes)} étapes",
            user_id=request.user_id
        )
        
        return jsonify({
            "success": True,
            "message": f"Workflow configuré avec {len(etapes)} étapes"
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@app.route("/documents/<int:doc_id>/workflow", methods=["GET"])
@token_required
def get_workflow_document(doc_id):
    """
    Voir l'état du workflow
    ---
    tags:
      - Workflow
    summary: Retourne l'historique des validations d'un document
    security:
      - Bearer: []
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Historique des validations
    """
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT v.id, v.statut, v.date_action, v.commentaire,
               n.nom_niveau, n.ordre, n.role_requis,
               u.nom as validateur_nom
        FROM validations_document v
        JOIN niveaux_validation n ON v.niveau_id = n.id
        LEFT JOIN users u ON v.validateur_id = u.id
        WHERE v.document_id = %s
        ORDER BY n.ordre ASC
    """, (doc_id,))
    
    validations = cur.fetchall()
    cur.close()
    
    result = []
    for v in validations:
        result.append({
            "id": v[0],
            "statut": v[1],
            "date": str(v[2]) if v[2] else None,
            "commentaire": v[3],
            "etape_nom": v[4],
            "etape_ordre": v[5],
            "role_requis": v[6],
            "valideur": v[7]
        })
    
    return jsonify({
        "success": True,
        "validations": result,
        "count": len(result)
    }), 200

@app.route("/documents/<int:doc_id>/valider-etape", methods=["PUT"])
@token_required
def valider_etape(doc_id):
    """
    Valider une étape du workflow
    ---
    tags:
      - Workflow
    summary: Valide l'étape courante et passe à la suivante
    security:
      - Bearer: []
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            commentaire:
              type: string
              example: Validé par le manager
    responses:
      200:
        description: Étape validée
      403:
        description: Rôle non autorisé
      404:
        description: Document non trouvé
    """
    data = request.json or {}
    commentaire = data.get("commentaire", "")
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            SELECT d.niveau_validation_actuel, d.auteur_id,
                   n.id, n.ordre, n.role_requis, n.nom_niveau,
                   (SELECT COUNT(*) FROM niveaux_validation nv 
                    WHERE nv.entreprise_id = (SELECT entreprise_id FROM users WHERE id = d.auteur_id)) as total_etapes
            FROM documents d
            LEFT JOIN niveaux_validation n ON n.entreprise_id = 
                (SELECT entreprise_id FROM users WHERE id = d.auteur_id)
                AND n.ordre = d.niveau_validation_actuel
            WHERE d.id = %s
        """, (doc_id,))
        
        result = cur.fetchone()
        
        if not result:
            cur.close()
            return jsonify({"message": "Document non trouvé"}), 404
        
        niveau_actuel, auteur_id, niveau_id, ordre, role_requis, nom_niveau, total_etapes = result
        
        if role_requis and request.user_role != role_requis:
            cur.close()
            return jsonify({
                "success": False,
                "message": f"Cette étape nécessite le rôle '{role_requis}'"
            }), 403
        
        if niveau_id:
            cur.execute("""
                UPDATE validations_document 
                SET statut = 'valide', validateur_id = %s, 
                    date_action = NOW(), commentaire = %s
                WHERE document_id = %s AND niveau_id = %s
            """, (request.user_id, commentaire, doc_id, niveau_id))
        
        if ordre < total_etapes:
            cur.execute("""
                UPDATE documents 
                SET niveau_validation_actuel = %s 
                WHERE id = %s
            """, (ordre + 1, doc_id))
            
            cur.execute("""
                INSERT INTO validations_document (document_id, niveau_id)
                SELECT %s, id FROM niveaux_validation 
                WHERE entreprise_id = (SELECT entreprise_id FROM users WHERE id = %s)
                AND ordre = %s
            """, (doc_id, auteur_id, ordre + 1))
            
            message = f"Étape '{nom_niveau}' validée. Prochaine étape: {ordre + 1}/{total_etapes}"
        else:
            cur.execute("""
                UPDATE documents 
                SET workflow_termine = TRUE, statut = 'valide' 
                WHERE id = %s
            """, (doc_id,))
            message = f"Workflow terminé! Document validé."
        
        mysql.connection.commit()
        
        ajouter_log(
            action='VALIDATION_ETAPE',
            description=f"Document {doc_id} - Étape {ordre}/{total_etapes} validée",
            user_id=request.user_id,
            document_id=doc_id
        )
        
        cur.close()
        return jsonify({
            "success": True,
            "message": message
        }), 200
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

# ============================================
# FICHIERS STATIQUES
# ============================================

@app.route('/sw.js')
def serve_sw():
    """Sert le service worker"""
    return send_from_directory('static', 'sw.js')

@app.route('/offline.html')
def serve_offline():
    """Sert la page hors-ligne"""
    return send_from_directory('static', 'offline.html')

@app.route('/offline-queue.js')
def serve_offline_queue():
    """Sert le script de file d'attente"""
    return send_from_directory('static', 'offline-queue.js')

@app.route('/index.html')
def serve_index():
    """Sert la page de test"""
    return send_from_directory('static', 'index.html')

@app.route('/test.html')
def serve_test():
    """Sert la page de test simple"""
    return send_from_directory('static', 'test.html')

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