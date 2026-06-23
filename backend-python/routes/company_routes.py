import json

from flask import request, jsonify
from werkzeug.security import generate_password_hash
from services.admin_service_orm import AdminService
from extensions import db
from models_sqlalchemy import Entreprise


from utils.company_logo import save_company_logo


def register_company_routes(app):

    @app.route("/api/company/register", methods=["POST"])
    def register_company():
        try:
            if request.content_type and 'multipart/form-data' in request.content_type:
                entreprise = json.loads(request.form.get('entreprise', '{}'))
                administrateur = json.loads(request.form.get('administrateur', '{}'))
                logo_file = request.files.get('logo')
            else:
                data = request.json or {}
                entreprise = data.get('entreprise')
                administrateur = data.get('administrateur')
                logo_file = None

            if not entreprise or not administrateur:
                return jsonify({"success": False, "message": "Données incomplètes"}), 400

            required = ['nom', 'nif', 'rccm', 'adresse', 'telephone', 'email']
            missing = [f for f in required if not (entreprise.get(f) or '').strip()]
            if missing:
                labels = {
                    'nom': "Nom de l'entreprise", 'nif': 'NIF', 'rccm': 'RCCM',
                    'adresse': 'Adresse', 'telephone': 'Téléphone', 'email': 'Email',
                }
                return jsonify({
                    "success": False,
                    "message": "Champs obligatoires manquants : " + ', '.join(labels.get(m, m) for m in missing),
                }), 400

            administrateur['password'] = generate_password_hash(administrateur.get('password'))
            result = AdminService.create_company_with_admin(entreprise, administrateur)

            if not result.get('success'):
                return jsonify({"success": False, "message": result.get('message')}), result.get('status_code', 400)

            entreprise_id = result['entreprise_id']
            if logo_file and logo_file.filename:
                logo_url = save_company_logo(entreprise_id, logo_file)
                if logo_url:
                    company = Entreprise.query.get(entreprise_id)
                    if company:
                        company.logo_url = logo_url
                        db.session.commit()

            return jsonify({
                "success": True,
                "message": "Entreprise et administrateur créés",
                "entreprise_id": entreprise_id,
            }), 201

        except Exception as e:
            print(f"[ERREUR] register_company: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
