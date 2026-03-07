# ============================================
# utils/file_upload.py - Gestionnaire d'upload
# Auteur: [Ton nom]
# Date: 7 Mars 2026
# ============================================

import os
import time
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    """
    Vérifie si l'extension du fichier est autorisée.
    
    Args:
        filename: Nom du fichier (ex: 'document.pdf')
    
    Returns:
        True si l'extension est autorisée, False sinon
    """
    # Vérifier que le fichier a une extension
    if '.' not in filename:
        return False
    
    # Récupérer l'extension (en minuscules)
    extension = filename.rsplit('.', 1)[1].lower()
    
    # Vérifier si elle est dans la liste des autorisées
    return extension in ALLOWED_EXTENSIONS


def get_file_size(file):
    """
    Récupère la taille d'un fichier uploadé.
    
    Args:
        file: Fichier uploadé (depuis request.files)
    
    Returns:
        Taille en octets
    """
    # Aller à la fin du fichier
    file.seek(0, os.SEEK_END)
    # Lire la position (taille)
    size = file.tell()
    # Revenir au début pour pouvoir lire le fichier
    file.seek(0)
    return size


def secure_filename_with_path(filename, user_id):
    """
    Génère un nom de fichier sécurisé avec identifiant unique.
    
    Args:
        filename: Nom original du fichier
        user_id: ID de l'utilisateur qui upload
    
    Returns:
        Nom sécurisé (ex: '5_1612345678_document.pdf')
    """
    # Nettoyer le nom (enlever caractères spéciaux, espaces)
    secure_name = secure_filename(filename)
    
    # Timestamp pour garantir l'unicité
    timestamp = str(int(time.time()))
    
    # Format: {user_id}_{timestamp}_{nom_nettoye}
    return f"{user_id}_{timestamp}_{secure_name}"