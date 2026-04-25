from flask import request, jsonify
from werkzeug.security import generate_password_hash
from utils.db import get_db

def register_company_routes(app):

    @app.route("/api/company/register", methods=["POST"])
    def register_company():
        try:
            data = request.json
            entreprise = data.get('entreprise')
            administrateur = data.get('administrateur')

            if not entreprise or not administrateur:
                return jsonify({"success": False, "message": "Données incomplètes"}), 400

            conn = get_db()
            cur = conn.cursor()

            # Vérifier si l'email admin existe déjà
            cur.execute("SELECT id FROM users WHERE email = %s", (administrateur.get('email'),))
            if cur.fetchone():
                cur.close()
                conn.close()
                return jsonify({"success": False, "message": "Cet email est déjà utilisé"}), 409

            # Créer l'entreprise
            cur.execute("""
                INSERT INTO entreprises (nom, email, telephone, adresse, statut)
                VALUES (%s, %s, %s, %s, 'actif')
            """, (
                entreprise.get('nom'),
                entreprise.get('email'),
                entreprise.get('telephone'),
                entreprise.get('adresse')
            ))
            entreprise_id = cur.lastrowid

            # Créer l'administrateur PME
            password_hash = generate_password_hash(administrateur.get('password'))

            cur.execute("""
                INSERT INTO users (nom, email, password, telephone, role, entreprise_id, actif)
                VALUES (%s, %s, %s, %s, 'admin_pme', %s, 1)
            """, (
                administrateur.get('nom'),
                administrateur.get('email'),
                password_hash,
                administrateur.get('telephone'),
                entreprise_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"success": True, "message": "Entreprise et administrateur créés"}), 201

        except Exception as e:
            print(f"[ERREUR] register_company: {e}")
            return jsonify({"success": False, "message": str(e)}), 500