from flask import request, jsonify
from werkzeug.security import generate_password_hash
from services.admin_service_orm import AdminService


def register_company_routes(app):

    @app.route("/api/company/register", methods=["POST"])
    def register_company():
        try:
            data = request.json
            entreprise = data.get('entreprise')
            administrateur = data.get('administrateur')

            if not entreprise or not administrateur:
                return jsonify({"success": False, "message": "Données incomplètes"}), 400

            administrateur['password'] = generate_password_hash(administrateur.get('password'))
            result = AdminService.create_company_with_admin(entreprise, administrateur)

            if not result.get('success'):
                return jsonify({"success": False, "message": result.get('message')}), result.get('status_code', 400)

            return jsonify({"success": True, "message": "Entreprise et administrateur créés", "entreprise_id": result['entreprise_id']}), 201

        except Exception as e:
            print(f"[ERREUR] register_company: {e}")
            return jsonify({"success": False, "message": str(e)}), 500