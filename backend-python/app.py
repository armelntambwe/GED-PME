# ==============================
# IMPORTS
# ==============================

from flask import Flask, request, jsonify   # Flask + gestion JSON
from flask_mysqldb import MySQL             # Connexion MySQL
from werkzeug.security import generate_password_hash, check_password_hash  # Hash mot de passe
from config import Config                   # Configuration DB
from utils.jwt_manager import generer_token # Gestionnaire JWT
from middleware.auth import token_required, role_required, get_current_user
from utils.logger import ajouter_log  # ← 
import os
from werkzeug.utils import secure_filename
from utils.file_upload import allowed_file, get_file_size, secure_filename_with_path
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS

from flask import send_file
import os
import mimetypes

# ==============================
# INITIALISATION APP
# ==============================

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)


# ==============================
# ROUTES
# ==============================

# Route principale
@app.route("/")
def home():
    return "GED-PME connecté à MySQL"


# Test connexion base
@app.route("/test-db")
def test_db():
    cur = mysql.connection.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    cur.close()
    return "Connexion MySQL OK" if result else "Erreur connexion"


# 🔐 Route inscription utilisateur
@app.route("/register", methods=["POST"])
def register():
    # Récupérer les données JSON envoyées
    data = request.json
    
    # Validation des données
    if not data or "nom" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "Données manquantes"}), 400
    
    # Extraire les champs
    nom = data["nom"]
    email = data["email"]
    role = data.get("role", "employe")  # Valeur par défaut: employé
    
    # Sécuriser le mot de passe
    password = generate_password_hash(data["password"])
    
    # Ouvrir curseur DB
    cur = mysql.connection.cursor()
    
    try:
        # Insertion dans la table users
        cur.execute(
            "INSERT INTO users (nom, email, password, role) VALUES (%s, %s, %s, %s)",
            (nom, email, password, role)
        )
        
        # Sauvegarder
        mysql.connection.commit()
        user_id = cur.lastrowid
        
        # Réponse JSON
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


# 🔑 Route login utilisateur
# ============================================
# ROUTE LOGIN (AUTHENTIFICATION)
# ============================================
# 🔑 Route login utilisateur
@app.route("/login", methods=["POST"])
def login():
    """
    Authentifie un utilisateur et retourne un token JWT.
    """
    
    # 1. Récupération des données JSON
    data = request.json
    print(f"📥 Données reçues: {data}")  # Debug
    
    # 2. Validation
    if not data or "email" not in data or "password" not in data:
        return jsonify({
            "success": False,
            "message": "Données manquantes. Champs requis: email, password"
        }), 400

    email = data["email"]
    password = data["password"]

    # 3. Recherche de l'utilisateur
    try:
        cur = mysql.connection.cursor()
        
        # Exécution de la requête
        cur.execute(
            "SELECT id, nom, password, role FROM users WHERE email = %s",
            (email,)  # Tuple avec une virgule
        )
        
        user = cur.fetchone()
        cur.close()

        # 4. Vérification existence
        if not user:
            print(f"❌ Utilisateur non trouvé: {email}")
            return jsonify({
                "success": False,
                "message": "Utilisateur non trouvé"
            }), 404

        # 5. Vérification mot de passe
        stored_password = user[2]
        
        if not check_password_hash(stored_password, password):
            print(f"❌ Mot de passe incorrect pour: {email}")
            return jsonify({
                "success": False,
                "message": "Mot de passe incorrect"
            }), 401

        # 6. Génération token JWT
        token = generer_token(user[0], user[3])
        print(f"✅ Connexion réussie: {user[1]} (ID: {user[0]})")

        # 7. Réponse
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
        print(f"❌ Erreur lors de la connexion: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erreur serveur: {str(e)}"
        }), 500
# 📄 Route pour créer un document
# 📄 Route pour créer un nouveau document
# URL: POST http://localhost:5000/documents
# Headers: Authorization: Bearer <token>
# Body: {"titre": "Mon document", "description": "Description"}
@app.route("/documents", methods=["POST"])
@token_required  # ← DÉCORATEUR : Vérifie que l'utilisateur est authentifié
def create_document():
    """
    Crée un nouveau document en statut BROUILLON.
    L'ID de l'utilisateur est automatiquement récupéré depuis le token JWT.
    
    Étapes:
        1. Récupérer les données JSON envoyées
        2. Valider que le titre est présent
        3. Récupérer l'ID de l'utilisateur depuis le token (request.user_id)
        4. Insérer le document en base avec statut 'brouillon'
        5. Retourner l'ID du document créé
    """
    
    # Étape 1: Récupération des données JSON envoyées par le client
    data = request.json
    
    # Étape 2: Validation des données
    if not data or "titre" not in data:
        return jsonify({
            "success": False,
            "message": "Titre requis"
        }), 400
    
    # Étape 3: Extraction des données
    titre = data["titre"]
    description = data.get("description", "")  # Description optionnelle
    
    # Étape 4: Récupération de l'ID depuis le token (SÉCURITÉ)
    # On utilise l'ID du token, pas celui envoyé par le client
    auteur_id = request.user_id  # ← Ceci vient du décorateur @token_required
    
    # Étape 5: Insertion en base de données
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            INSERT INTO documents (titre, description, auteur_id, statut)
            VALUES (%s, %s, %s, 'brouillon')
        """, (titre, description, auteur_id))
        
        doc_id = cur.lastrowid  # Récupère l'ID auto-généré
        mysql.connection.commit()
        
        # Étape 6: Réponse de succès
        return jsonify({
            "success": True,
            "message": "Document créé avec succès",
            "document_id": doc_id,
            "statut": "brouillon"
        }), 201
        
    except Exception as e:
        # En cas d'erreur, annuler la transaction
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500
    finally:
        # Toujours fermer le curseur
        cur.close()


# 📋 Route pour lister les documents
# URL: GET http://localhost:5000/documents?user_id=1&statut=soumis
# Headers: Authorization: Bearer <token>
# Paramètres optionnels:
#   - user_id: filtrer par utilisateur
#   - statut: filtrer par statut (brouillon, soumis, valide, rejete, archive)
@app.route("/documents", methods=["GET"])
@token_required  # ← DÉCORATEUR : Vérifie que l'utilisateur est authentifié
def get_documents():
    """
    Récupère la liste des documents avec filtres optionnels.
    Les employés ne peuvent voir que leurs propres documents.
    Les administrateurs peuvent tout voir.
    
    Paramètres GET:
        user_id: ID de l'utilisateur (optionnel)
        statut: Statut des documents (optionnel)
    """
    
    # Étape 1: Récupération des paramètres de filtrage
    user_id = request.args.get("user_id")
    statut = request.args.get("statut")
    
    # Étape 2: Vérification des droits (SÉCURITÉ)
    # Si l'utilisateur est un employé, il ne peut voir que ses propres documents
    if request.user_role == 'employe':
        # Si l'employé essaie de voir les documents d'un autre utilisateur
        if user_id and int(user_id) != request.user_id:
            return jsonify({
                "success": False,
                "message": "Vous ne pouvez voir que vos propres documents"
            }), 403
        # Si l'employé n'a pas précisé d'user_id, on force le filtre sur lui-même
        if not user_id:
            user_id = str(request.user_id)
    
    # Étape 3: Construction de la requête SQL
    cur = mysql.connection.cursor()
    
    # Requête de base (on sélectionne uniquement les colonnes nécessaires)
    query = "SELECT id, titre, description, date_creation, statut, auteur_id FROM documents WHERE 1=1"
    params = []
    
    # Ajout du filtre utilisateur si présent
    if user_id:
        query += " AND auteur_id = %s"
        params.append(user_id)
    
    # Ajout du filtre statut si présent
    if statut:
        query += " AND statut = %s"
        params.append(statut)
    
    # Tri par date décroissante (plus récent en premier)
    query += " ORDER BY date_creation DESC"
    
    # Étape 4: Exécution de la requête
    cur.execute(query, params)
    documents = cur.fetchall()
    cur.close()
    
    # Étape 5: Conversion des résultats en dictionnaires (format JSON)
    result = []
    for doc in documents:
        # doc[0] = id
        # doc[1] = titre
        # doc[2] = description
        # doc[3] = date_creation
        # doc[4] = statut
        # doc[5] = auteur_id
        result.append({
            "id": doc[0],
            "titre": doc[1],
            "description": doc[2],
            "date_creation": str(doc[3]),  # Conversion en string pour JSON
            "statut": doc[4],
            "auteur_id": doc[5]
        })
    
    # Étape 6: Retour de la réponse
    return jsonify({
        "success": True,
        "count": len(result),      # Nombre de documents trouvés
        "documents": result         # Liste des documents
    })
# ✅ Route pour valider un document (Admin uniquement)
# URL: PUT http://localhost:5000/documents/6/valider
# Headers: Authorization: Bearer <token_admin>
@app.route("/documents/<int:doc_id>/valider", methods=["PUT"])
@token_required                      # ← Vérifie l'authentification
@role_required(['admin_global', 'admin_pme'])  # ← Vérifie le rôle admin
def valider_document(doc_id):
    """
    Valide un document soumis.
    Change le statut de 'soumis' à 'valide'.
    Seul un administrateur peut valider des documents.
    
    Args:
        doc_id: ID du document à valider (récupéré depuis l'URL)
    """
    
    # Étape 1: L'ID de l'admin est automatiquement récupéré depuis le token
    # Plus besoin de recevoir admin_id dans le body (SÉCURITÉ)
    validateur_id = request.user_id
    
    cur = mysql.connection.cursor()
    
    try:
        # Étape 2: Vérifier que le document existe et est en statut 'soumis'
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
        
        # Étape 3: Mise à jour du document
        # NOW() est une fonction MySQL qui donne la date/heure actuelle
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
        
        # Étape 4: Vérification du nombre de lignes affectées
        if cur.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Document non trouvé ou déjà traité"
            }), 404
        
        # Étape 5: Réponse de succès
        return jsonify({
            "success": True,
            "message": "Document validé avec succès"
        }), 200
        
    except Exception as e:
        # En cas d'erreur, annuler la transaction
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500
    finally:
        # Toujours fermer le curseur
        cur.close()

# ❌ Route pour rejeter un document
# ❌ Route pour rejeter un document (Admin uniquement)
# URL: PUT http://localhost:5000/documents/6/rejeter
# Headers: Authorization: Bearer <token_admin>
# Body: {"commentaire": "Document incomplet, veuillez ajouter la signature"}
@app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
@token_required                      # ← Vérifie l'authentification
@role_required(['admin_global', 'admin_pme'])  # ← Vérifie le rôle admin
def rejeter_document(doc_id):
    """
    Rejette un document soumis avec un commentaire.
    Change le statut de 'soumis' à 'rejete'.
    Seul un administrateur peut rejeter des documents.
    
    Args:
        doc_id: ID du document à rejeter (récupéré depuis l'URL)
    
    Body JSON:
        commentaire: Motif du rejet (obligatoire)
    """
    
    # Étape 1: Récupération des données JSON
    data = request.json
    
    # Étape 2: Validation des données
    if not data or "commentaire" not in data:
        return jsonify({
            "success": False,
            "message": "Commentaire requis pour expliquer le rejet"
        }), 400
    
    # Étape 3: L'ID de l'admin est automatiquement récupéré depuis le token
    validateur_id = request.user_id
    commentaire = data["commentaire"]
    
    cur = mysql.connection.cursor()
    
    try:
        # Étape 4: Vérifier que le document existe et est en statut 'soumis'
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
        
        # Étape 5: Mise à jour du document avec le commentaire de rejet
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
        
        # Étape 6: Vérification du nombre de lignes affectées
        if cur.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Document non trouvé ou déjà traité"
            }), 404
        
        # Étape 7: Réponse de succès
        return jsonify({
            "success": True,
            "message": "Document rejeté",
            "commentaire": commentaire  # On renvoie le commentaire pour confirmation
        }), 200
        
    except Exception as e:
        # En cas d'erreur, annuler la transaction
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500
    finally:
        # Toujours fermer le curseur
        cur.close()


        # 📤 Route pour soumettre un document (passer de BROUILLON à SOUMIS)


# ============================================
# SOUMETTRE UN DOCUMENT (AVEC WORKFLOW)
# ============================================
@app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
@token_required
def soumettre_document(doc_id):
    """
    📤 SOUMETTRE UN DOCUMENT POUR VALIDATION
    ---
    Soumet un document et démarre le workflow de validation.
    """
    
    cur = mysql.connection.cursor()
    
    try:
        # ===== ÉTAPE 1 : VÉRIFIER LE PROPRIÉTAIRE =====
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
        
        # ===== ÉTAPE 2 : RÉCUPÉRER L'ENTREPRISE DE L'UTILISATEUR =====
        cur.execute("SELECT entreprise_id FROM users WHERE id = %s", (request.user_id,))
        user_entreprise = cur.fetchone()
        
        if not user_entreprise or not user_entreprise[0]:
            # Pas de multi-entreprise, workflow simple
            cur.execute("""
                UPDATE documents SET statut = 'soumis' WHERE id = %s
            """, (doc_id,))
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
        
        # ===== ÉTAPE 3 : RÉCUPÉRER LA PREMIÈRE ÉTAPE DU WORKFLOW =====
        cur.execute("""
            SELECT id FROM niveaux_validation 
            WHERE entreprise_id = %s
            ORDER BY ordre ASC LIMIT 1
        """, (entreprise_id,))
        
        premiere_etape = cur.fetchone()
        
        if premiere_etape:
            # Workflow personnalisé
            niveau_id = premiere_etape[0]
            
            # Créer l'entrée dans validations_document
            cur.execute("""
                INSERT INTO validations_document (document_id, niveau_id)
                VALUES (%s, %s)
            """, (doc_id, niveau_id))
            
            # Mettre à jour le document
            cur.execute("""
                UPDATE documents 
                SET statut = 'soumis', niveau_validation_actuel = 1 
                WHERE id = %s
            """, (doc_id,))
            
            # Compter le nombre total d'étapes
            cur.execute("SELECT COUNT(*) FROM niveaux_validation WHERE entreprise_id = %s", (entreprise_id,))
            total_etapes = cur.fetchone()[0]
            
            message = f"Document soumis - Étape 1/{total_etapes}"
        else:
            # Pas de workflow configuré, validation simple
            cur.execute("""
                UPDATE documents SET statut = 'soumis' WHERE id = %s
            """, (doc_id,))
            message = "Document soumis pour validation"
        
        mysql.connection.commit()
        
        # ===== ÉTAPE 4 : LOG =====
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
    
# ============================================
# ROUTE TEST PROTÉGÉE
# ============================================
@app.route("/profile", methods=["GET"])
@token_required
def profile():
    """
    Route test pour vérifier que l'authentification fonctionne.
    """
    return jsonify({
        "success": True,
        "user_id": request.user_id,
        "role": request.user_role,
        "message": "Accès autorisé !"
    }), 200

# ============================================
# ROUTE D'UPLOAD DE FICHIERS
# ============================================
@app.route("/documents/upload", methods=["POST"])
@token_required
def upload_document():
    """
    📤 UPLOAD DE FICHIER
    ---
    Permet à un utilisateur authentifié d'uploader un document.
    Le fichier est stocké sur le disque et une entrée est créée en base.
    
    Format attendu: multipart/form-data
    Champs:
        - file: (obligatoire) Le fichier à uploader
        - titre: (optionnel) Titre du document (sinon nom du fichier)
        - description: (optionnel) Description
        - categorie_id: (optionnel) ID de la catégorie
    """
    
    # ===== ÉTAPE 1 : VÉRIFICATION DU FICHIER =====
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
    
    # ===== ÉTAPE 2 : VALIDATION DE L'EXTENSION =====
    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": f"Format non autorisé. Formats acceptés: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 415
    
    # ===== ÉTAPE 3 : VALIDATION DE LA TAILLE =====
    file_size = get_file_size(file)
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({
            "success": False,
            "message": f"Fichier trop volumineux. Taille max: {MAX_CONTENT_LENGTH/1024/1024:.0f} Mo"
        }), 413
    
    # ===== ÉTAPE 4 : PRÉPARATION DU STOCKAGE =====
    try:
        # Générer un nom de fichier unique et sécurisé
        secure_name = secure_filename_with_path(file.filename, request.user_id)
        
        # Créer le chemin complet
        filepath = os.path.join(UPLOAD_FOLDER, secure_name)
        
        # ===== ÉTAPE 5 : SAUVEGARDE DU FICHIER =====
        file.save(filepath)
        
        # ===== ÉTAPE 6 : RÉCUPÉRATION DES MÉTADONNÉES =====
        titre = request.form.get('titre', file.filename)
        description = request.form.get('description', '')
        categorie_id = request.form.get('categorie_id')
        
        # ===== ÉTAPE 7 : ENREGISTREMENT EN BASE =====
        cur = mysql.connection.cursor()
        
        query = """
            INSERT INTO documents 
            (titre, description, fichier_nom, fichier_chemin, fichier_taille, 
             type_mime, auteur_id, statut, categorie_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'brouillon', %s)
        """
        params = (
            titre, 
            description, 
            file.filename,  # Nom original pour l'affichage
            filepath,       # Chemin physique pour le téléchargement
            file_size,      # Taille en octets
            file.mimetype,  # Type MIME (ex: application/pdf)
            request.user_id,
            categorie_id
        )
        
        cur.execute(query, params)
        doc_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        
        ajouter_log(
    action='CREATION',
    description=f"Document '{titre}' uploadé",
    user_id=request.user_id,
    document_id=doc_id
)
        # ===== ÉTAPE 8 : RÉPONSE SUCCÈS =====
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
        # En cas d'erreur, nettoyer le fichier si déjà créé
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            "success": False,
            "message": f"Erreur lors de l'upload: {str(e)}"
        }), 500


# ============================================
# ROUTE DE TÉLÉCHARGEMENT
# ============================================
from flask import send_file
import os
import mimetypes

@app.route("/documents/<int:doc_id>/download", methods=["GET"])
@token_required
def download_document(doc_id):
    """
    📥 TÉLÉCHARGEMENT DE FICHIER
    ---
    Permet à un utilisateur authentifié de télécharger un document.
    
    Args:
        doc_id: ID du document à télécharger
    
    Retour:
        - Le fichier (200) si succès
        - 404 si document non trouvé
        - 403 si accès non autorisé
        - 404 si fichier manquant sur disque
    """
    
    # ===== ÉTAPE 1 : RÉCUPÉRER LES INFOS DU DOCUMENT =====
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT titre, fichier_chemin, auteur_id 
        FROM documents 
        WHERE id = %s
    """, (doc_id,))
    
    doc = cur.fetchone()
    cur.close()
    
    # Vérifier que le document existe
    if not doc:
        return jsonify({
            "success": False,
            "message": "Document non trouvé"
        }), 404
    
    titre, fichier_chemin, auteur_id = doc
    
    # ===== ÉTAPE 2 : VÉRIFICATION DES DROITS =====
    # Règles :
    # - Admin peut tout voir
    # - Employé ne peut voir que ses documents
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
    # ===== ÉTAPE 3 : VÉRIFIER QUE LE FICHIER EXISTE =====
    if not os.path.exists(fichier_chemin):
        return jsonify({
            "success": False,
            "message": "Fichier introuvable sur le serveur"
        }), 404
    
    # ===== ÉTAPE 4 : JOURNALISATION (optionnelle) =====
    # On ajoutera un log plus tard
    print(f"📥 Téléchargement: doc {doc_id} par user {request.user_id}")
    
    # ===== ÉTAPE 5 : ENVOYER LE FICHIER =====
    try:
        return send_file(
            fichier_chemin,
            as_attachment=True,  # Force le téléchargement
            download_name=titre,  # Nom du fichier proposé
            mimetype=mimetypes.guess_type(fichier_chemin)[0]
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors du téléchargement: {str(e)}"
        }), 500
    

    # ============================================
# ROUTES POUR LES CATÉGORIES
# ============================================

@app.route("/categories", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def create_category():
    """
    📁 CRÉER UNE CATÉGORIE
    ---
    Permet à un admin de créer une nouvelle catégorie.
    
    Body (JSON):
        - nom: (obligatoire) Nom de la catégorie
        - description: (optionnelle) Description
    
    Retour:
        - 201: Catégorie créée
        - 400: Données manquantes
        - 409: Catégorie déjà existante
    """
    
    # ===== ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES =====
    data = request.json
    
    if not data or "nom" not in data:
        return jsonify({
            "success": False,
            "message": "Le nom de la catégorie est requis"
        }), 400
    
    nom = data["nom"].strip()
    description = data.get("description", "")
    
    # ===== ÉTAPE 2 : VÉRIFIER QUE LA CATÉGORIE N'EXISTE PAS =====
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE nom = %s", (nom,))
    existing = cur.fetchone()
    
    if existing:
        cur.close()
        return jsonify({
            "success": False,
            "message": f"Une catégorie '{nom}' existe déjà"
        }), 409
    
    # ===== ÉTAPE 3 : INSÉRER LA NOUVELLE CATÉGORIE =====
    try:
        cur.execute("""
            INSERT INTO categories (nom, description)
            VALUES (%s, %s)
        """, (nom, description))
        
        category_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        
        # ===== ÉTAPE 4 : RETOURNER LA CATÉGORIE CRÉÉE =====
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


        # ============================================
# LISTER LES CATÉGORIES
# ============================================
@app.route("/categories", methods=["GET"])
@token_required
def get_categories():
    """
    📋 LISTER LES CATÉGORIES
    ---
    Retourne la liste de toutes les catégories.
    Accessible à tous les utilisateurs authentifiés.
    
    Retour:
        - 200: Liste des catégories
    """
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, nom, description, date_creation 
        FROM categories 
        ORDER BY nom ASC
    """)
    
    categories = cur.fetchall()
    cur.close()
    
    # Convertir les tuples en dictionnaires
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
    
# ============================================
# MODIFIER UNE CATÉGORIE
# ============================================
@app.route("/categories/<int:categorie_id>", methods=["PUT"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def update_category(categorie_id):
    """
    ✏️ MODIFIER UNE CATÉGORIE
    ---
    Permet à un admin de modifier une catégorie existante.
    
    Args:
        categorie_id: ID de la catégorie à modifier
    
    Body (JSON):
        - nom: (optionnel) Nouveau nom
        - description: (optionnel) Nouvelle description
    
    Retour:
        - 200: Catégorie modifiée
        - 404: Catégorie non trouvée
        - 409: Nom déjà utilisé
    """
    
    # ===== ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES =====
    data = request.json
    
    if not data or ("nom" not in data and "description" not in data):
        return jsonify({
            "success": False,
            "message": "Rien à modifier. Fournissez 'nom' ou 'description'."
        }), 400
    
    # ===== ÉTAPE 2 : VÉRIFIER QUE LA CATÉGORIE EXISTE =====
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nom, description FROM categories WHERE id = %s", (categorie_id,))
    category = cur.fetchone()
    
    if not category:
        cur.close()
        return jsonify({
            "success": False,
            "message": "Catégorie non trouvée"
        }), 404
    
    # ===== ÉTAPE 3 : SI LE NOM EST MODIFIÉ, VÉRIFIER QU'IL N'EXISTE PAS DÉJÀ =====
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
    
    # ===== ÉTAPE 4 : CONSTRUIRE LA REQUÊTE DE MISE À JOUR =====
    updates = []
    params = []
    
    if "nom" in data:
        updates.append("nom = %s")
        params.append(data["nom"])
    
    if "description" in data:
        updates.append("description = %s")
        params.append(data["description"])
    
    params.append(categorie_id)
    
    # ===== ÉTAPE 5 : EXÉCUTER LA MISE À JOUR =====
    try:
        query = f"UPDATE categories SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        mysql.connection.commit()
        
        # Récupérer la catégorie mise à jour
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

# ============================================
# SUPPRIMER UNE CATÉGORIE
# ============================================
@app.route("/categories/<int:categorie_id>", methods=["DELETE"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def delete_category(categorie_id):
    """
    🗑️ SUPPRIMER UNE CATÉGORIE
    ---
    Permet à un admin de supprimer une catégorie.
    Les documents liés à cette catégorie auront categorie_id = NULL.
    
    Args:
        categorie_id: ID de la catégorie à supprimer
    
    Retour:
        - 200: Catégorie supprimée
        - 404: Catégorie non trouvée
        - 409: Catégorie utilisée (optionnel)
    """
    
    # ===== ÉTAPE 1 : VÉRIFIER QUE LA CATÉGORIE EXISTE =====
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nom FROM categories WHERE id = %s", (categorie_id,))
    category = cur.fetchone()
    
    if not category:
        cur.close()
        return jsonify({
            "success": False,
            "message": "Catégorie non trouvée"
        }), 404
    
    # ===== ÉTAPE 2 : OPTIONNEL - VÉRIFIER SI DES DOCUMENTS SONT LIÉS =====
    cur.execute("SELECT COUNT(*) FROM documents WHERE categorie_id = %s", (categorie_id,))
    count = cur.fetchone()[0]
    
    # ===== ÉTAPE 3 : SUPPRIMER LA CATÉGORIE =====
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
# CONFIGURATION DU WORKFLOW DE VALIDATION
# ============================================
@app.route("/entreprise/workflow", methods=["POST"])
@token_required
@role_required(['admin_global', 'admin_pme'])
def configurer_workflow():
    """
    🔧 CONFIGURER LE WORKFLOW DE VALIDATION
    ---
    Permet à un admin de définir les étapes de validation pour son entreprise.
    
    Body (JSON):
        - etapes: Liste des étapes avec pour chacune:
            - nom: Nom de l'étape (ex: "Chef d'équipe")
            - role: Rôle requis ('admin_global', 'admin_pme', 'manager', 'employe')
            - delai: (optionnel) Délai en heures (défaut: 48)
    
    Exemple:
    {
        "etapes": [
            {"nom": "Chef d'équipe", "role": "employe", "delai": 24},
            {"nom": "Manager", "role": "admin_pme", "delai": 48},
            {"nom": "Direction", "role": "admin_global"}
        ]
    }
    """
    
    # ===== ÉTAPE 1 : RÉCUPÉRER L'ENTREPRISE DE L'UTILISATEUR =====
    # On récupère l'entreprise_id de l'utilisateur connecté
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
    
    # ===== ÉTAPE 2 : RÉCUPÉRER LES DONNÉES =====
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
    
    # ===== ÉTAPE 3 : SUPPRIMER L'ANCIENNE CONFIGURATION =====
    try:
        # Supprimer les anciennes étapes de cette entreprise
        cur.execute("DELETE FROM niveaux_validation WHERE entreprise_id = %s", (entreprise_id,))
        
        # ===== ÉTAPE 4 : AJOUTER LES NOUVELLES ÉTAPES =====
        for i, etape in enumerate(etapes, 1):
            # Valider que le rôle est correct
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
        
        # ===== ÉTAPE 5 : JOURNALISATION =====
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

        # ============================================
# VOIR L'ÉTAT DU WORKFLOW D'UN DOCUMENT
# ============================================
@app.route("/documents/<int:doc_id>/workflow", methods=["GET"])
@token_required
def get_workflow_document(doc_id):
    """
    📋 VOIR L'ÉTAT DU WORKFLOW D'UN DOCUMENT
    ---
    Retourne l'historique des validations pour un document.
    """
    
    cur = mysql.connection.cursor()
    
    # Récupérer les validations
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



# ============================================
# VALIDER UNE ÉTAPE DU WORKFLOW
# ============================================
@app.route("/documents/<int:doc_id>/valider-etape", methods=["PUT"])
@token_required
def valider_etape(doc_id):
    """
    ✅ VALIDER UNE ÉTAPE DU WORKFLOW
    ---
    Valide l'étape courante et passe à l'étape suivante.
    
    Body (optionnel):
        - commentaire: Commentaire sur la validation
    """
    
    data = request.json or {}
    commentaire = data.get("commentaire", "")
    
    cur = mysql.connection.cursor()
    
    try:
        # ===== ÉTAPE 1 : RÉCUPÉRER L'ÉTAPE COURANTE =====
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
        
        # ===== ÉTAPE 2 : VÉRIFIER LE RÔLE =====
        if role_requis and request.user_role != role_requis:
            cur.close()
            return jsonify({
                "success": False,
                "message": f"Cette étape nécessite le rôle '{role_requis}'"
            }), 403
        
        # ===== ÉTAPE 3 : MARQUER L'ÉTAPE COMME VALIDÉE =====
        if niveau_id:
            cur.execute("""
                UPDATE validations_document 
                SET statut = 'valide', validateur_id = %s, 
                    date_action = NOW(), commentaire = %s
                WHERE document_id = %s AND niveau_id = %s
            """, (request.user_id, commentaire, doc_id, niveau_id))
        
        # ===== ÉTAPE 4 : PASSER À L'ÉTAPE SUIVANTE =====
        if ordre < total_etapes:
            # Il reste des étapes
            cur.execute("""
                UPDATE documents 
                SET niveau_validation_actuel = %s 
                WHERE id = %s
            """, (ordre + 1, doc_id))
            
            # Créer l'entrée pour la prochaine étape
            cur.execute("""
                INSERT INTO validations_document (document_id, niveau_id)
                SELECT %s, id FROM niveaux_validation 
                WHERE entreprise_id = (SELECT entreprise_id FROM users WHERE id = %s)
                AND ordre = %s
            """, (doc_id, auteur_id, ordre + 1))
            
            message = f"Étape '{nom_niveau}' validée. Prochaine étape: {ordre + 1}/{total_etapes}"
        else:
            # Workflow terminé
            cur.execute("""
                UPDATE documents 
                SET workflow_termine = TRUE, statut = 'valide' 
                WHERE id = %s
            """, (doc_id,))
            message = f"Workflow terminé! Document validé."
        
        mysql.connection.commit()
        
        # ===== ÉTAPE 5 : LOG =====
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
# ROUTES POUR LES FICHIERS STATIQUES
# ============================================
from flask import send_from_directory

@app.route('/<path:filename>')
def serve_static(filename):
    """
    Sert les fichiers statiques (sw.js, offline.html, etc.)
    """
    return send_from_directory('static', filename)

@app.route('/sw.js')
def serve_sw():
    """
    Sert spécifiquement le service worker à la racine
    """
    return send_from_directory('static', 'sw.js')


# ==============================
# LANCEMENT SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 GED-PME - Serveur démarré")
    print("📝 URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)