# ============================================
# middleware/auth.py 
# ============================================
# Corrections apportées :
#   ✅ Ajout de request.user_entreprise_id
#   ✅ Gestion du token Bearer propre
#   ✅ Messages d'erreur clairs
# ============================================

from functools import wraps
from flask import request, jsonify
from utils.jwt_manager import verifier_token


def token_required(f):
    """
    Décorateur : vérifie que le token JWT est présent et valide.
    Expose sur l'objet request :
        - request.user_id
        - request.user_role
        - request.user_entreprise_id  ← ✅ NOUVEAU (était manquant)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({
                    "success": False,
                    "message": "Format du token invalide. Attendu : Bearer <token>"
                }), 401

        if not token:
            return jsonify({
                "success": False,
                "message": "Token d'authentification manquant"
            }), 401

        try:
            payload = verifier_token(token)

            # ✅ Les 3 attributs disponibles dans toutes les routes
            request.user_id            = payload['user_id']
            request.user_role          = payload['role']
            request.user_entreprise_id = payload.get('entreprise_id')  # None si admin_global

        except Exception:
            return jsonify({
                "success": False,
                "message": "Token invalide ou expiré. Veuillez vous reconnecter."
            }), 401

        return f(*args, **kwargs)
    return decorated


def role_required(roles_autorises):
    """
    Décorateur : vérifie que l'utilisateur a l'un des rôles autorisés.
    Doit être utilisé APRÈS @token_required.

    Exemple :
        @token_required
        @role_required(['admin_global', 'admin_pme'])
        def ma_route(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user_role'):
                return jsonify({
                    "success": False,
                    "message": "Authentification requise"
                }), 401

            if request.user_role not in roles_autorises:
                return jsonify({
                    "success": False,
                    "message": f"Accès refusé. Rôle requis : {', '.join(roles_autorises)}"
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    """
    Retourne un dict avec les infos de l'utilisateur courant.
    Utilise les attributs posés par @token_required.
    """
    return {
        "user_id":       getattr(request, 'user_id', None),
        "role":          getattr(request, 'user_role', None),
        "entreprise_id": getattr(request, 'user_entreprise_id', None),
    }
