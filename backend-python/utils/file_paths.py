"""Résolution des chemins de fichiers uploadés."""
import os
import mimetypes

from config import UPLOAD_FOLDER


def resolve_document_path(stored_path):
    """
    Retourne le chemin absolu d'un fichier document s'il existe sur le disque.
    Gère les chemins relatifs (uploads/...) et les noms de fichier seuls.
    """
    if not stored_path:
        return None

    candidates = []
    if os.path.isabs(stored_path):
        candidates.append(stored_path)
    else:
        candidates.append(os.path.abspath(stored_path))
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(base, stored_path))
        candidates.append(os.path.join(base, UPLOAD_FOLDER, os.path.basename(stored_path)))
        candidates.append(os.path.join(UPLOAD_FOLDER, os.path.basename(stored_path)))
        candidates.append(os.path.join(os.getcwd(), stored_path))
        candidates.append(os.path.join(os.getcwd(), UPLOAD_FOLDER, os.path.basename(stored_path)))

    seen = set()
    for path in candidates:
        norm = os.path.normpath(path)
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.isfile(norm):
            return norm
    return None


def guess_mime(filename, stored_mime=None):
    """Déduit le type MIME à partir du nom de fichier si nécessaire."""
    if stored_mime and stored_mime not in ('application/octet-stream', 'binary/octet-stream', ''):
        return stored_mime
    guessed, _ = mimetypes.guess_type(filename or '')
    return guessed or stored_mime or 'application/octet-stream'
