# ============================================
# middleware/auth.py - Middleware d'authentification JWT
# ============================================
from functools import wraps
from flask import request, jsonify, current_app
import jwt

def token_required(f):
    """
    Décorateur qui vérifie que la requête contient un token JWT valide.
    À appliquer sur toutes les routes protégées.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Récupérer le token du header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            # Format attendu: "Bearer <token>"
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # 2. Vérifier que le token existe
        if not token:
            return jsonify({
                "success": False,
                "message": "Token manquant. Authentification requise."
            }), 401
        
        try:
            # 3. Vérifier et décoder le token
            secret_key = current_app.config['JWT_SECRET_KEY']
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # 4. Ajouter les infos du token à la requête
            request.user_id = payload['user_id']
            request.user_role = payload['role']
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "message": "Token expiré. Veuillez vous reconnecter."
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "success": False,
                "message": "Token invalide."
            }), 401
        
        # 5. Continuer vers la route protégée
        return f(*args, **kwargs)
    
    return decorated


def role_required(allowed_roles):
    """
    Décorateur qui vérifie que l'utilisateur a le rôle approprié.
    À utiliser APRÈS @token_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Vérifier que l'utilisateur est authentifié
            if not hasattr(request, 'user_role'):
                return jsonify({
                    "success": False,
                    "message": "Authentification requise."
                }), 401
            
            # Vérifier le rôle
            if request.user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": f"Accès interdit. Rôle requis: {', '.join(allowed_roles)}"
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    """
    Helper pour récupérer l'utilisateur actuel depuis la requête.
    """
    if hasattr(request, 'user_id'):
        return {
            'id': request.user_id,
            'role': request.user_role
        }
    return None