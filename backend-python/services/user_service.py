# services/user_service.py - Version corrigée

from extensions import db
from models_sqlalchemy import User, Entreprise, Log
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service pour les opérations sur les utilisateurs utilisant ORM SQLAlchemy."""
    
    # ==================== AUTHENTIFICATION ====================
    
    @staticmethod
    def get_user_by_email(email: str) -> dict:
        """Récupère un utilisateur par email."""
        try:
            user = User.query.filter_by(email=email).first()
            if user:
                return user.to_dict()
            return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_email: {e}")
            raise

    @staticmethod
    def get_user_by_email_raw(email: str):
        """Récupère l'objet utilisateur SQLAlchemy par email."""
        try:
            return User.query.filter_by(email=email).first()
        except Exception as e:
            logger.error(f"Erreur get_user_by_email_raw: {e}")
            raise
    
    @staticmethod
    def get_user_by_id(user_id: int) -> dict:
        """Récupère un utilisateur par ID."""
        try:
            user = User.query.get(user_id)
            if user:
                return user.to_dict()
            return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_id: {e}")
            raise
    
    @staticmethod
    def create_user(nom: str, email: str, password_hash: str, role: str = 'employe',
                   telephone: str = '', entreprise_id: int = None) -> int:
        """Crée un nouvel utilisateur et retourne son ID."""
        try:
            user = User(
                nom=nom,
                email=email,
                password=password_hash,
                role=role,
                telephone=telephone or '',
                entreprise_id=entreprise_id,
                actif=True,
                date_inscription=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            return user.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_user: {e}")
            raise
    
    @staticmethod
    def get_users(entreprise_id: int = None, role: str = None, limit: int = 100) -> list:
        """Récupère une liste d'utilisateurs avec filtres optionnels."""
        try:
            query = User.query
            
            if entreprise_id:
                query = query.filter_by(entreprise_id=entreprise_id)
            
            if role:
                query = query.filter_by(role=role)
            
            users = query.limit(limit).all()
            return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"Erreur get_users: {e}")
            raise
    
    @staticmethod
    def update_user_status(user_id: int, actif: bool) -> bool:
        """Active ou désactive un utilisateur."""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            user.actif = actif
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_user_status: {e}")
            raise
    
    @staticmethod
    def update_user_password(user_id: int, password_hash: str) -> bool:
        """Met à jour le mot de passe d'un utilisateur."""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            user.password = password_hash
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_user_password: {e}")
            raise
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Supprime un utilisateur."""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            db.session.delete(user)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur delete_user: {e}")
            raise
    
    @staticmethod
    def count_users(entreprise_id: int = None) -> int:
        """Compte le nombre total d'utilisateurs."""
        try:
            query = User.query
            if entreprise_id:
                query = query.filter_by(entreprise_id=entreprise_id)
            return query.count()
        except Exception as e:
            logger.error(f"Erreur count_users: {e}")
            raise
    
    # ==================== RECHERCHE & FILTRAGE ====================
    
    @staticmethod
    def search_users(search_term: str, entreprise_id: int = None, limit: int = 50) -> list:
        """Recherche des utilisateurs par nom ou email."""
        try:
            query = User.query
            
            if entreprise_id:
                query = query.filter_by(entreprise_id=entreprise_id)
            
            query = query.filter(
                (User.nom.ilike(f'%{search_term}%')) |
                (User.email.ilike(f'%{search_term}%'))
            )
            
            users = query.limit(limit).all()
            return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"Erreur search_users: {e}")
            raise
    
    @staticmethod
    def update_user(user_id: int, nom: str = None, telephone: str = None) -> bool:
        """Met à jour les informations d'un utilisateur."""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            if nom is not None:
                user.nom = nom
            if telephone is not None:
                user.telephone = telephone
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_user: {e}")
            raise

    # ==================== SUPPRIMEES TEMPORAIREMENT ====================
    # Les méthodes create_employe_complet, update_employe_complet, 
    # update_last_login et get_employe_details sont commentées car elles
    # utilisent des colonnes qui n'existent pas encore dans la base.
    
    # @staticmethod
    # def generate_matricule():
    #     ...
    
    # @staticmethod 
    # def create_employe_complet(data: dict, entreprise_id: int) -> int:
    #     ...
    
    # @staticmethod
    # def update_employe_complet(user_id: int, data: dict) -> bool:
    #     ...
    
    # @staticmethod
    # def update_last_login(user_id: int) -> bool:
    #     ...
    
    # @staticmethod
    # def get_employe_details(user_id: int) -> dict:
    #     ...