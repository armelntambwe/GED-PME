# services/auth_service.py
# Service d'authentification - Logique métier

from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from models.log import Log
from utils.jwt_manager import generer_token

class AuthService:
    """Service d'authentification - Gère l'inscription et la connexion"""

    @staticmethod
    def register(nom, email, password, role='employe', telephone=None, entreprise_id=1):
        """
        Inscription d'un nouvel utilisateur
        Retourne: (success, message, user_id)
        """
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.find_by_email(email)
        if existing_user:
            return False, "Cet email est déjà utilisé", None

        # Hasher le mot de passe
        password_hash = generate_password_hash(password)

        # Créer l'utilisateur
        user_id = User.create(nom, email, password_hash, role, telephone, entreprise_id)

        # Journaliser l'action
        Log.create('INSCRIPTION', f"Nouvel utilisateur créé : {email}", user_id)

        return True, "Utilisateur créé avec succès", user_id

    @staticmethod
    def login(email, password):
        """
        Connexion d'un utilisateur
        Retourne: (success, message, token, user)
        """
        # Chercher l'utilisateur par email
        user = User.find_by_email(email)

        if not user:
            return False, "Email non trouvé", None, None

        # Vérifier le mot de passe
        if not check_password_hash(user['password'], password):
            return False, "Mot de passe incorrect", None, None

        # Vérifier si le compte est actif
        if user.get('actif', 1) == 0:
            return False, "Compte désactivé", None, None

        # Générer le token JWT
        token = generer_token(user['id'], user['role'], user.get('entreprise_id'))

        # Journaliser l'action
        Log.create('CONNEXION', f"Connexion de {email}", user['id'])

        return True, "Connexion réussie", token, user

    @staticmethod
    def logout(user_id):
        """
        Déconnexion d'un utilisateur
        Retourne: (success, message)
        """
        Log.create('DECONNEXION', f"Déconnexion de l'utilisateur {user_id}", user_id)
        return True, "Déconnexion réussie"