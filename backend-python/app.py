# ==============================
# IMPORTS
# ==============================

from flask import Flask, request, jsonify   # Flask + gestion JSON
from flask_mysqldb import MySQL             # Connexion MySQL
from werkzeug.security import generate_password_hash  # Hash mot de passe
from config import Config                   # Configuration DB
from werkzeug.security import check_password_hash  # Vérifier mot de passe

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

    # Extraire les champs
    nom = data["nom"]
    email = data["email"]

    # Sécuriser le mot de passe
    password = generate_password_hash(data["password"])

    # Ouvrir curseur DB
    cur = mysql.connection.cursor()

    # Insertion dans la table users
    cur.execute(
        "INSERT INTO users (nom, email, password) VALUES (%s, %s, %s)",
        (nom, email, password)
    )

    # Sauvegarder
    mysql.connection.commit()

    # Fermer curseur
    cur.close()

    # Réponse JSON
    return jsonify({"message": "Utilisateur créé avec succès"})


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
# ==============================
# LANCEMENT SERVEUR
# ==============================

if __name__ == "__main__":
    app.run(debug=True)