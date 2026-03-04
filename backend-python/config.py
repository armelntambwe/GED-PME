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