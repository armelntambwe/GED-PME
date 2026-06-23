import re

from extensions import db
from models_sqlalchemy import Indexation


class IndexationService:
    """Indexation des métadonnées et du contenu OCR pour la recherche."""

    STOP_WORDS = {
        'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'en', 'au', 'aux',
        'the', 'and', 'for', 'with', 'this', 'that', 'from',
    }

    @staticmethod
    def _extract_keywords(text, limit=40):
        if not text:
            return []
        tokens = re.findall(r'[a-zA-ZÀ-ÿ0-9]{3,}', text.lower())
        seen = set()
        keywords = []
        for token in tokens:
            if token in IndexationService.STOP_WORDS or token in seen:
                continue
            seen.add(token)
            keywords.append(token)
            if len(keywords) >= limit:
                break
        return keywords

    @staticmethod
    def index_document(document_id, titre=None, description=None, contenu_ocr=None):
        Indexation.query.filter_by(document_id=document_id).delete()

        parts = []
        if titre:
            parts.append(titre)
        if description:
            parts.append(description)
        if contenu_ocr:
            parts.append(contenu_ocr)

        keywords = IndexationService._extract_keywords(' '.join(parts))
        for mot in keywords:
            db.session.add(Indexation(document_id=document_id, mot_cle=mot))

        db.session.commit()
        return keywords
