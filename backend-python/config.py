# config.py
import os

class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'ged_pme_test'

    SECRET_KEY = 'votre-cle-secrete-tres-longue-et-difficile-a-deviner'

    JWT_SECRET_KEY = 'votre-cle-secrete-tres-longue-2025'
    JWT_EXPIRATION_HOURS = 24

    # Configuration SQLAlchemy (pour ORM existant)
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration pour SQLAlchemy Core (nouveau)
    DATABASE_URL_CORE = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"


# Variables en dehors de la classe pour l'import direct
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'md', 'csv', 'json', 'xml', 'html', 'htm', 'rtf',
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg',
    'mp4', 'webm', 'mp3', 'wav', 'ogg',
    'zip', 'rar', '7z',
}

# Email optionnel (envoi de documents)
MAIL_ENABLED = os.environ.get('MAIL_ENABLED', 'false').lower() == 'true'
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
MAIL_FROM = os.environ.get('MAIL_FROM', MAIL_USERNAME or 'ged-pme@local')

# WhatsApp — alertes automatiques (validation, rejet, publication…)
WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'true').lower() == 'true'
WHATSAPP_PROVIDER = os.environ.get('WHATSAPP_PROVIDER', 'callmebot').lower()
DEFAULT_PHONE_PREFIX = os.environ.get('DEFAULT_PHONE_PREFIX', '+243')
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:5000')

WHATSAPP_IMPORTANT_TYPES = [
    'DOCUMENT_VALIDE', 'DOCUMENT_REJETE', 'DOCUMENT_PUBLIE',
    'DOCUMENT_SOUMIS', 'DOCUMENT_OBSOLETE', 'DOCUMENT_DETRUIT',
]

# Twilio WhatsApp
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', '')

# Meta WhatsApp Cloud API
WHATSAPP_META_TOKEN = os.environ.get('WHATSAPP_META_TOKEN', '')
WHATSAPP_META_PHONE_ID = os.environ.get('WHATSAPP_META_PHONE_ID', '')

# CallMeBot (gratuit — chaque utilisateur active son numéro et sa clé API)
CALLMEBOT_API_KEY = os.environ.get('CALLMEBOT_API_KEY', '')