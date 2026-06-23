from extensions import db

from .entreprise import Entreprise
from .user import User
from .document import Document
from .categorie import Categorie
from .log import Log
from .version import VersionDocument 
from .notification import Notification
from .workflow_config import WorkflowConfig
from .archive import ArchiveDocument
from .indexation import Indexation

__all__ = [
    'db',
    'Entreprise',
    'User',
    'Document',
    'Categorie',
    'Log',
    'VersionDocument',
    'Notification',
    'WorkflowConfig',
    'ArchiveDocument',
    'Indexation',
]
