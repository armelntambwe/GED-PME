# ============================================
# utils/jwt_manager.py - Gestionnaire JWT
# ============================================
import jwt
import datetime
from flask import current_app


def generer_token(user_id, role, entreprise_id=None):
    """
    Génère un token JWT pour un utilisateur authentifié.
    Le token expire après 24 heures.

    Args:
        user_id      : ID de l'utilisateur
        role         : Rôle (admin_global, admin_pme, employe)
        entreprise_id: ID de l'entreprise — ✅ AJOUT (était absent)
    """
    secret_key = current_app.config['JWT_SECRET_KEY']

    # ✅ CORRECTION : entreprise_id inclus dans le payload
    payload = {
        'user_id':      user_id,
        'role':         role,
        'entreprise_id': entreprise_id,   # None pour admin_global sans entreprise
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }

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