# routes/user_routes.py
import json
from flask import request, jsonify
from middleware.auth import token_required, role_required
from services.user_service import UserService
from models_sqlalchemy import User, Entreprise, Log, Notification
from extensions import db
from werkzeug.security import generate_password_hash
from utils.company_logo import save_company_logo
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def register_user_routes(app):

    @app.route("/users", methods=["GET"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def get_users():
        try:
            query = User.query
            if request.user_role == 'admin_pme':
                query = query.filter(User.entreprise_id == request.user_entreprise_id)
            users = query.order_by(User.id.desc()).all()
            return jsonify({"success": True, "users": [u.to_dict() for u in users]}), 200
        except Exception as e:
            logger.error(f"Erreur get_users: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/users/<int:user_id>/desactiver", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def desactiver_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            user.actif = False
            db.session.add(user)

            log = Log(
                action='DESACTIVATION_USER',
                description=f"Utilisateur {user_id} désactivé",
                user_id=request.user_id,
                date_action=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({"success": True, "message": "Utilisateur désactivé"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur desactiver_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/users/<int:user_id>/activer", methods=["PUT"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def activer_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            user.actif = True
            db.session.add(user)

            log = Log(
                action='ACTIVATION_USER',
                description=f"Utilisateur {user_id} activé",
                user_id=request.user_id,
                date_action=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({"success": True, "message": "Utilisateur activé"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur activer_user: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/admin/employes", methods=["GET"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def get_employes():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            query = User.query.filter_by(role='employe')
            if entreprise_id is not None:
                query = query.filter_by(entreprise_id=entreprise_id)
            employes = query.order_by(User.id.desc()).all()
            return jsonify({"success": True, "employes": [u.to_dict() for u in employes]}), 200
        except Exception as e:
            logger.error(f"Erreur get_employes: {e}")
            return jsonify({"success": True, "employes": []}), 200

    @app.route("/admin/employes", methods=["POST"])
    @token_required
    @role_required(['admin_global', 'admin_pme'])
    def create_employe():
        try:
            data = request.json or {}
            nom = data.get('nom', '').strip()
            email = data.get('email', '').strip()
            telephone = data.get('telephone', '').strip()
            password = data.get('password', 'employe123')

            if not nom or not email:
                return jsonify({"success": False, "message": "Nom et email requis"}), 400
            if len(password) < 6:
                return jsonify({"success": False, "message": "Le mot de passe doit avoir au moins 6 caractères"}), 400

            existing_user = UserService.get_user_by_email(email)
            if existing_user:
                return jsonify({"success": False, "message": "Email déjà utilisé"}), 409

            entreprise_id = getattr(request, 'user_entreprise_id', None)
            password_hash = generate_password_hash(password)
            user_id = UserService.create_user(
                nom=nom,
                email=email,
                password_hash=password_hash,
                role='employe',
                telephone=telephone,
                entreprise_id=entreprise_id
            )

            log = Log(
                action='CREATION_EMPLOYE',
                description=f"Employé '{nom}' créé",
                user_id=request.user_id,
                date_action=datetime.utcnow()
            )
            db.session.add(log)

            notification = Notification(
                user_id=request.user_id,
                type_notif='EMPLOYE_CREE',
                message=f"L'employé {nom} a été créé",
                lien='/dashboard-pme?tab=employes',
                lue=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Employé créé", "user_id": user_id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_employe: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/info", methods=["GET"])
    @token_required
    def get_api_entreprise_info():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            return jsonify({
                "success": True,
                "id": entreprise.id,
                "nom": entreprise.nom,
                "nif": entreprise.nif or '',
                "rccm": entreprise.rccm or '',
                "secteur_activite": entreprise.secteur_activite or '',
                "logo_url": entreprise.logo_url or '',
                "adresse": entreprise.adresse or '',
                "telephone": entreprise.telephone or '',
                "email": entreprise.email or ''
            }), 200
        except Exception as e:
            logger.error(f"Erreur get_api_entreprise_info: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/info", methods=["PUT"])
    @token_required
    @role_required(['admin_pme'])
    def update_api_entreprise_info():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = json.loads(request.form.get('entreprise', '{}'))
                logo_file = request.files.get('logo')
            else:
                data = request.json or {}
                logo_file = None

            entreprise = Entreprise.query.get(entreprise_id)
            if not entreprise:
                return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404

            if 'nom' in data:
                entreprise.nom = (data.get('nom') or '').strip() or entreprise.nom
            if 'adresse' in data:
                entreprise.adresse = data.get('adresse', entreprise.adresse)
            if 'telephone' in data:
                entreprise.telephone = data.get('telephone', entreprise.telephone)
            if 'email' in data:
                entreprise.email = data.get('email', entreprise.email)
            if 'nif' in data:
                entreprise.nif = (data.get('nif') or '').strip()
            if 'rccm' in data:
                entreprise.rccm = (data.get('rccm') or '').strip()
            if 'secteur_activite' in data:
                entreprise.secteur_activite = (data.get('secteur_activite') or '').strip()

            if logo_file and logo_file.filename:
                logo_url = save_company_logo(entreprise_id, logo_file)
                if logo_url:
                    entreprise.logo_url = logo_url

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Entreprise mise à jour",
                "logo_url": entreprise.logo_url or ''
            }), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_api_entreprise_info: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/2fa/setup", methods=["POST"])
    @token_required
    def setup_2fa():
        """Génère un secret TOTP (sans activer tant que le code n'est pas validé)."""
        try:
            from utils.totp_helper import generate_secret, provisioning_uri
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            secret = generate_secret()
            user.totp_secret = secret
            user.totp_enabled = False
            db.session.commit()
            uri = provisioning_uri(secret, user.email)
            return jsonify({
                "success": True,
                "secret": secret,
                "otpauth_uri": uri,
                "message": "Scannez le QR code ou saisissez le secret dans Google Authenticator, puis validez avec un code.",
            }), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur setup_2fa: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/2fa/enable", methods=["POST"])
    @token_required
    def enable_2fa():
        try:
            from utils.totp_helper import verify_totp
            data = request.json or {}
            code = data.get('code', '')
            user = User.query.get(request.user_id)
            if not user or not user.totp_secret:
                return jsonify({"success": False, "message": "Configurez d'abord la 2FA"}), 400
            if not verify_totp(user.totp_secret, code):
                return jsonify({"success": False, "message": "Code incorrect"}), 400
            user.totp_enabled = True
            db.session.commit()
            return jsonify({"success": True, "message": "Double authentification activée"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/2fa/disable", methods=["POST"])
    @token_required
    def disable_2fa():
        try:
            from utils.totp_helper import verify_totp
            from werkzeug.security import check_password_hash
            data = request.json or {}
            code = data.get('code', '')
            password = data.get('password', '')
            user = User.query.get(request.user_id)
            if not user or not user.totp_enabled:
                return jsonify({"success": False, "message": "2FA non active"}), 400
            if not check_password_hash(user.password, password):
                return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401
            if not verify_totp(user.totp_secret, code):
                return jsonify({"success": False, "message": "Code incorrect"}), 400
            user.totp_enabled = False
            user.totp_secret = None
            db.session.commit()
            return jsonify({"success": True, "message": "Double authentification désactivée"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/profile", methods=["GET"])
    @token_required
    def get_api_user_profile():
        try:
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            return jsonify({"success": True, **user.to_dict()}), 200
        except Exception as e:
            logger.error(f"Erreur get_api_user_profile: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/profile", methods=["PUT"])
    @token_required
    def update_api_user_profile():
        try:
            data = request.json or {}
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404

            if 'nom' in data:
                user.nom = data.get('nom', user.nom)
            if 'telephone' in data:
                user.telephone = data.get('telephone', user.telephone)
            if 'poste' in data:
                user.poste = data.get('poste', user.poste)
            if 'service' in data:
                user.service = data.get('service', user.service)
            if 'notify_whatsapp' in data:
                user.notify_whatsapp = bool(data.get('notify_whatsapp'))
            if 'whatsapp_api_key' in data:
                key = (data.get('whatsapp_api_key') or '').strip()
                user.whatsapp_api_key = key or None
            if 'password' in data and data.get('password'):
                if len(data.get('password')) < 6:
                    return jsonify({"success": False, "message": "Le mot de passe doit avoir au moins 6 caractères"}), 400
                user.password = generate_password_hash(data.get('password'))

            db.session.commit()
            return jsonify({"success": True, "message": "Profil mis à jour"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_api_user_profile: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/whatsapp/status", methods=["GET"])
    @token_required
    def whatsapp_status():
        try:
            from utils.whatsapp_helper import is_whatsapp_configured, check_callmebot_connectivity
            from config import WHATSAPP_PROVIDER, WHATSAPP_ENABLED
            provider = (WHATSAPP_PROVIDER or 'callmebot').lower()
            network_ok, network_detail = (True, '')
            if provider == 'callmebot':
                network_ok, network_detail = check_callmebot_connectivity()
            return jsonify({
                "success": True,
                "enabled": WHATSAPP_ENABLED,
                "configured": is_whatsapp_configured(),
                "provider": provider,
                "network_ok": network_ok,
                "network_detail": network_detail,
            }), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/user/whatsapp/test", methods=["POST"])
    @token_required
    def whatsapp_test():
        try:
            from utils.whatsapp_helper import send_test_alert
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            if not user.notify_whatsapp:
                return jsonify({"success": False, "message": "Activez d'abord les alertes WhatsApp dans votre profil"}), 400
            if not user.telephone:
                return jsonify({"success": False, "message": "Renseignez votre numéro de téléphone dans le profil"}), 400
            from config import WHATSAPP_PROVIDER
            provider = (WHATSAPP_PROVIDER or 'callmebot').lower()
            if provider == 'callmebot':
                from utils.whatsapp_helper import check_callmebot_connectivity
                net_ok, net_msg = check_callmebot_connectivity()
                if not net_ok:
                    return jsonify({"success": False, "message": net_msg}), 503
                if not (user.whatsapp_api_key or '').strip():
                    from config import CALLMEBOT_API_KEY
                    if not (CALLMEBOT_API_KEY or '').strip():
                        return jsonify({
                            "success": False,
                            "message": "Clé API CallMeBot manquante — activez CallMeBot sur WhatsApp puis enregistrez la clé dans votre profil",
                        }), 400
            ok, detail = send_test_alert(user)
            if ok:
                return jsonify({"success": True, "message": detail}), 200
            return jsonify({"success": False, "message": detail}), 503
        except Exception as e:
            logger.error(f"Erreur whatsapp_test: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entreprise/logs", methods=["GET"])
    @token_required
    @role_required(['admin_pme'])
    def get_api_entreprise_logs():
        try:
            entreprise_id = getattr(request, 'user_entreprise_id', None)
            if entreprise_id is None:
                return jsonify({"success": False, "message": "Entreprise non identifiée"}), 400

            logs = Log.query.join(User, Log.user_id == User.id).filter(User.entreprise_id == entreprise_id).order_by(Log.date_action.desc()).limit(50).all()
            return jsonify({"success": True, "logs": [log.to_dict() for log in logs]}), 200
        except Exception as e:
            logger.error(f"Erreur get_api_entreprise_logs: {e}")
            return jsonify({"success": True, "logs": []}), 200
