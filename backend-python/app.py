# ==============================
# IMPORTS
# ==============================

from flask import Flask, request, jsonify   # Flask + gestion JSON
from flask_mysqldb import MySQL             # Connexion MySQL
from werkzeug.security import generate_password_hash, check_password_hash  # Hash mot de passe
from config import Config                   # Configuration DB
from utils.jwt_manager import generer_token # Gestionnaire JWT
from middleware.auth import token_required, role_required, get_current_user
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
# URL: PUT http://localhost:5000/documents/6/soumettre
# Headers: Authorization: Bearer <token>
@app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
@token_required  # ← DÉCORATEUR : Vérifie que l'utilisateur est authentifié
def soumettre_document(doc_id):
    """
    Soumet un document pour validation.
    Change le statut de 'brouillon' à 'soumis'.
    Seul le propriétaire du document peut le soumettre.
    
    Args:
        doc_id: ID du document à soumettre (récupéré depuis l'URL)
    """
    
    cur = mysql.connection.cursor()
    
    try:
        # Étape 1: Vérifier que l'utilisateur est le propriétaire du document
        # On récupère l'auteur du document
        cur.execute("SELECT auteur_id, statut FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        
        # Si le document n'existe pas
        if not doc:
            cur.close()
            return jsonify({
                "success": False,
                "message": "Document non trouvé"
            }), 404
        
        # Vérification du propriétaire (SÉCURITÉ)
        if doc[0] != request.user_id:
            cur.close()
            return jsonify({
                "success": False,
                "message": "Vous ne pouvez soumettre que vos propres documents"
            }), 403
        
        # Vérification du statut (un document déjà soumis ne peut pas l'être à nouveau)
        if doc[1] != 'brouillon':
            cur.close()
            return jsonify({
                "success": False,
                "message": f"Impossible de soumettre un document en statut '{doc[1]}'"
            }), 400
        
        # Étape 2: Mise à jour du statut
        cur.execute("""
            UPDATE documents 
            SET statut = 'soumis' 
            WHERE id = %s AND statut = 'brouillon'
        """, (doc_id,))
        
        mysql.connection.commit()
        
        # Étape 3: Vérification que la mise à jour a bien eu lieu
        if cur.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Document déjà soumis ou non modifiable"
            }), 400
        
        # Étape 4: Réponse de succès
        return jsonify({
            "success": True,
            "message": "Document soumis pour validation"
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

# ==============================
# LANCEMENT SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 GED-PME - Serveur démarré")
    print("📝 URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)