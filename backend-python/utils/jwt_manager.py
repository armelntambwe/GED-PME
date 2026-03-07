# ============================================
# utils/jwt_manager.py - Gestionnaire JWT
# ============================================
import jwt
import datetime
from flask import current_app

def generer_token(user_id, role):
    """
    Génère un token JWT pour un utilisateur authentifié.
    Le token expire après 24 heures.
    """
    # Récupère la clé secrète depuis la configuration Flask
    secret_key = current_app.config['JWT_SECRET_KEY']
    
    # Crée le payload (données du token)
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()  # Date de création
    }
    
    # Génère le token avec l'algorithme HS256
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    
    return token


def verifier_token(token):
    """
    Vérifie la validité d'un token JWT.
    Retourne le payload si valide, None sinon.
    """
    secret_key = current_app.config['JWT_SECRET_KEY']
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expiré")
        return None
    except jwt.InvalidTokenError:
        print("Token invalide")
        return None