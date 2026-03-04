# ==============================
# IMPORTS
# ==============================

from flask import Flask, request, jsonify   # Flask + gestion JSON
from flask_mysqldb import MySQL             # Connexion MySQL
from werkzeug.security import generate_password_hash, check_password_hash  # Hash mot de passe
from config import Config                   # Configuration DB

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
@app.route("/login", methods=["POST"])
def login():
    data = request.json  # récupérer données JSON

    # Vérifier que les champs existent
    if not data or "email" not in data or "password" not in data:
        return jsonify({"message": "Données manquantes"}), 400

    email = data["email"]
    password = data["password"]

    cur = mysql.connection.cursor()

    # Rechercher utilisateur par email
    cur.execute(
        "SELECT id, nom, password, role FROM users WHERE email = %s",
        (email,)
    )

    user = cur.fetchone()
    cur.close()

    # Si utilisateur inexistant
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    stored_password = user[2]

    # Vérifier mot de passe hashé
    if not check_password_hash(stored_password, password):
        return jsonify({"message": "Mot de passe incorrect"}), 401

    # Connexion réussie
    return jsonify({
        "message": "Connexion réussie",
        "user": {
            "id": user[0],
            "nom": user[1],
            "role": user[3]
        }
    })


# 📄 Route pour créer un document
@app.route("/documents", methods=["POST"])
def create_document():
    data = request.json
    
    # Validation
    if not data or "titre" not in data or "user_id" not in data:
        return jsonify({"message": "Données manquantes"}), 400
    
    titre = data["titre"]
    description = data.get("description", "")
    auteur_id = data["user_id"]
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            INSERT INTO documents (titre, description, auteur_id, statut)
            VALUES (%s, %s, %s, 'brouillon')
        """, (titre, description, auteur_id))
        
        doc_id = cur.lastrowid
        mysql.connection.commit()
        
        return jsonify({
            "message": "Document créé",
            "document_id": doc_id,
            "statut": "brouillon"
        }), 201
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()


# 📋 Route pour lister les documents (CORRIGÉE)
@app.route("/documents", methods=["GET"])
def get_documents():
    user_id = request.args.get("user_id")
    statut = request.args.get("statut")
    
    cur = mysql.connection.cursor()
    
    # Construction de la requête
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
    
    # Convertir les tuples en dictionnaires
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


# 📤 Route pour soumettre un document
@app.route("/documents/<int:doc_id>/soumettre", methods=["PUT"])
def soumettre_document(doc_id):
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            UPDATE documents 
            SET statut = 'soumis' 
            WHERE id = %s AND statut = 'brouillon'
        """, (doc_id,))
        
        mysql.connection.commit()
        
        if cur.rowcount == 0:
            return jsonify({"message": "Document non trouvé ou déjà soumis"}), 404
            
        return jsonify({"message": "Document soumis pour validation"})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()


# ✅ Route pour valider un document
@app.route("/documents/<int:doc_id>/valider", methods=["PUT"])
def valider_document(doc_id):
    data = request.json
    
    if not data or "admin_id" not in data:
        return jsonify({"message": "admin_id requis"}), 400
        
    validateur_id = data["admin_id"]
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            UPDATE documents 
            SET statut = 'valide', 
                validateur_id = %s, 
                date_validation = NOW() 
            WHERE id = %s AND statut = 'soumis'
        """, (validateur_id, doc_id))
        
        mysql.connection.commit()
        
        if cur.rowcount == 0:
            return jsonify({"message": "Document non trouvé ou déjà traité"}), 404
            
        return jsonify({"message": "Document validé"})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()


# ❌ Route pour rejeter un document
@app.route("/documents/<int:doc_id>/rejeter", methods=["PUT"])
def rejeter_document(doc_id):
    data = request.json
    
    if not data or "admin_id" not in data or "commentaire" not in data:
        return jsonify({"message": "admin_id et commentaire requis"}), 400
    
    validateur_id = data["admin_id"]
    commentaire = data["commentaire"]
    
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("""
            UPDATE documents 
            SET statut = 'rejete', 
                validateur_id = %s, 
                commentaire_rejet = %s 
            WHERE id = %s AND statut = 'soumis'
        """, (validateur_id, commentaire, doc_id))
        
        mysql.connection.commit()
        
        if cur.rowcount == 0:
            return jsonify({"message": "Document non trouvé ou déjà traité"}), 404
            
        return jsonify({"message": "Document rejeté", "commentaire": commentaire})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()


# ==============================
# LANCEMENT SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 GED-PME - Serveur démarré")
    print("📝 URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)