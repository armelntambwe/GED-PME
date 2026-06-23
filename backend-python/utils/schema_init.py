"""Initialise / met à jour le schéma MySQL au démarrage."""
from sqlalchemy import inspect, text
from extensions import db
import logging

logger = logging.getLogger(__name__)


def _column_exists(insp, table, column):
    if table not in insp.get_table_names():
        return False
    return column in {c['name'] for c in insp.get_columns(table)}


def _add_column(insp, table, column, col_def):
    if not _column_exists(insp, table, column):
        db.session.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def}"))
        db.session.commit()
        logger.info("Colonne ajoutée: %s.%s", table, column)


def ensure_schema(app):
    """Crée les tables manquantes et ajoute les colonnes récentes."""
    with app.app_context():
        import models_sqlalchemy  # noqa: F401 — enregistre les modèles

        db.create_all()
        insp = inspect(db.engine)

        _add_column(insp, 'categories', 'entreprise_id', 'INT NULL')
        _add_column(insp, 'categories', 'created_at', 'DATETIME NULL')
        _add_column(insp, 'categories', 'updated_at', 'DATETIME NULL')
        _add_column(insp, 'documents', 'contenu_ocr', 'TEXT NULL')
        _add_column(insp, 'documents', 'date_modification', 'DATETIME NULL')
        _add_column(insp, 'documents', 'categorie_id', 'INT NULL')
        _add_column(insp, 'logs', 'document_id', 'INT NULL')
        _add_column(insp, 'logs', 'adresse_ip', 'VARCHAR(45) NULL')

        _add_column(insp, 'documents', 'date_detruit', 'DATETIME NULL')
        _add_column(insp, 'documents', 'date_publication', 'DATETIME NULL')
        _add_column(insp, 'documents', 'date_obsolete', 'DATETIME NULL')
        _add_column(insp, 'documents', 'version_actuelle', 'INT DEFAULT 1')
        _add_column(insp, 'users', 'poste', 'VARCHAR(100) NULL')
        _add_column(insp, 'users', 'service', 'VARCHAR(100) NULL')
        _add_column(insp, 'users', 'photo_url', 'VARCHAR(255) NULL')
        _add_column(insp, 'users', 'notify_whatsapp', 'TINYINT(1) DEFAULT 0')
        _add_column(insp, 'users', 'whatsapp_api_key', 'VARCHAR(64) NULL')
        _add_column(insp, 'users', 'totp_secret', 'VARCHAR(64) NULL')
        _add_column(insp, 'users', 'totp_enabled', 'TINYINT(1) DEFAULT 0')

        _add_column(insp, 'entreprises', 'nif', 'VARCHAR(50) NULL')
        _add_column(insp, 'entreprises', 'rccm', 'VARCHAR(50) NULL')
        _add_column(insp, 'entreprises', 'secteur_activite', 'VARCHAR(100) NULL')
        _add_column(insp, 'entreprises', 'logo_url', 'VARCHAR(255) NULL')

        missing_tables = {'versions_documents', 'logs', 'notifications', 'archives', 'indexations'} - set(insp.get_table_names())
        if missing_tables:
            db.create_all()
            logger.info("Tables créées: %s", ', '.join(sorted(missing_tables)))

        from services.category_service import CategoryService
        CategoryService.migrate_orphan_categories()
