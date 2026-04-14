# services/admin_service.py
# Service administrateur - Logique métier pour l'Admin Global

from models.entreprise import Entreprise
from models.user import User
from models.document import Document
from models.log import Log
from models.notification import Notification
from config import UPLOAD_FOLDER
import os
import shutil

class AdminService:
    """Service administrateur - Gestion globale du système"""

    @staticmethod
    def get_global_stats():
        """
        Récupère les statistiques globales
        Retourne: dict
        """
        entreprises = Entreprise.get_all()
        documents = Document.get_all()
        users = User.get_all()

        return {
            "total_entreprises": len(entreprises),
            "total_documents": len(documents),
            "total_users": len(users),
            "docs_en_attente": len(Document.get_by_status('soumis'))
        }

    @staticmethod
    def get_all_entreprises():
        """Récupère toutes les entreprises avec leurs statistiques"""
        return Entreprise.get_all()

    @staticmethod
    def create_entreprise(nom, adresse=None, telephone=None, email=None):
        """Crée une nouvelle entreprise"""
        entreprise_id = Entreprise.create(nom, adresse, telephone, email)
        return True, "Entreprise créée", entreprise_id

    @staticmethod
    def update_entreprise(entreprise_id, nom=None, adresse=None, telephone=None, email=None):
        """Met à jour une entreprise"""
        Entreprise.update(entreprise_id, nom, adresse, telephone, email)
        return True, "Entreprise modifiée"

    @staticmethod
    def toggle_entreprise(entreprise_id):
        """Active ou suspend une entreprise"""
        nouvel_etat = Entreprise.toggle_status(entreprise_id)
        if nouvel_etat is None:
            return False, "Entreprise non trouvée"
        return True, f"Entreprise {nouvel_etat}"

    @staticmethod
    def get_entreprise_stats(entreprise_id):
        """Récupère les statistiques d'une entreprise"""
        return Entreprise.get_stats(entreprise_id)

    @staticmethod
    def get_all_users():
        """Récupère tous les utilisateurs"""
        return User.get_all()

    @staticmethod
    def get_all_documents(limit=100):
        """Récupère tous les documents"""
        return Document.get_all(limit)

    @staticmethod
    def get_all_logs(limit=200):
        """Récupère tous les logs"""
        return Log.get_all(limit)

    @staticmethod
    def get_storage_info():
        """Récupère les informations de stockage"""
        total, used, free = shutil.disk_usage(UPLOAD_FOLDER)

        # Calculer la taille des fichiers uploadés
        total_upload = 0
        for dirpath, _, filenames in os.walk(UPLOAD_FOLDER):
            for f in filenames:
                total_upload += os.path.getsize(os.path.join(dirpath, f))

        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "uploads_mb": round(total_upload / (1024**2), 2)
        }

    @staticmethod
    def get_evolution(weeks=8):
        """Récupère l'évolution des documents"""
        return Document.get_evolution(None, weeks)