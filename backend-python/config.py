class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'ged_pme'

    SECRET_KEY = 'votre-cle-secrete-tres-longue-et-difficile-a-deviner'

    JWT_SECRET_KEY = 'votre-cle-secrete-tres-longue-2025'
    JWT_EXPIRATION_HOURS = 24


# Variables en dehors de la classe pour l'import direct
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'txt'}