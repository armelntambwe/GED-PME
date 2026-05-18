# ============================================
# utils/logger.py - Gestionnaire de logs (ORM)
# ============================================
from datetime import datetime
from extensions import db
from models_sqlalchemy import Log
import logging

logger = logging.getLogger(__name__)


def ajouter_log(action, description, user_id, document_id=None, adresse_ip=None):
    """Ajoute une entrée dans la table `logs` via SQLAlchemy ORM."""
    try:
        log = Log(
            action=action,
            description=description,
            user_id=user_id,
            document_id=document_id,
            adresse_ip=adresse_ip,
            date_action=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        return log.id
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur ajouter_log: {e}")
        raise