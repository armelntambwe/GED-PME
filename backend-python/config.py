class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'ged_pme'

    # Clé secrète pour les sessions et tokens JWT
    # En production, utiliser une variable d'environnement
    SECRET_KEY = 'votre-clé-secrète-très-longue-et-difficile-à-deviner'
    
    # ==============================
    # CONFIGURATION DES FICHIERS
    # ==============================
    
    # Dossier où seront stockés les fichiers uploadés
    UPLOAD_FOLDER = 'uploads'
    
    # Taille maximale des fichiers (16 Mo)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

     # CONFIGURATION JWT (À AJOUTER)
    # ==============================
    JWT_SECRET_KEY = 'votre-clé-secrète-très-longue-2025'
    JWT_EXPIRATION_HOURS = 24

    # ==============================
# CONFIGURATION UPLOAD (À AJOUTER)
# ==============================

# Dossier où seront stockés les fichiers
UPLOAD_FOLDER = 'uploads'

# Taille maximale des fichiers (16 Mo = 16 * 1024 * 1024)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Formats de fichiers autorisés (pour commencer)
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'txt'}