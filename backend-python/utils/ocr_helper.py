# utils/ocr_helper.py
"""Configuration et exécution OCR (Tesseract)."""
import os
import logging

logger = logging.getLogger(__name__)

TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\xampp\htdocs\tesseract\tesseract.exe',
]


def configure_tesseract():
    """Configure le chemin Tesseract si disponible."""
    import pytesseract
    for path in TESSERACT_PATHS:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


def extract_text_from_file(filepath):
    """
    Extrait le texte d'une image ou PDF.
    Retourne (texte, erreur_message).
    """
    from utils.file_paths import resolve_document_path
    resolved = resolve_document_path(filepath)
    if not resolved:
        return None, 'Fichier introuvable'

    ext = os.path.splitext(resolved)[1].lower()
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    try:
        import pytesseract
        from PIL import Image

        if not configure_tesseract():
            return None, (
                'Tesseract OCR non installé. Installez-le depuis '
                'https://github.com/UB-Mannheim/tesseract/wiki'
            )

        if ext in image_exts:
            text = pytesseract.image_to_string(Image.open(resolved), lang='fra+eng')
            return (text or '').strip(), None

        if ext == '.pdf':
            try:
                from pdf2image import convert_from_path
                pages = convert_from_path(resolved, dpi=200)
                parts = []
                for page in pages[:10]:
                    parts.append(pytesseract.image_to_string(page, lang='fra+eng'))
                return '\n'.join(parts).strip(), None
            except ImportError:
                return None, 'pdf2image requis pour OCR PDF: pip install pdf2image'
            except Exception as e:
                return None, f'Erreur OCR PDF: {e}'

        if ext == '.txt':
            with open(resolved, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip(), None

        return None, f'Format non supporté pour OCR: {ext}'

    except ImportError as e:
        return None, f'Dépendance OCR manquante: {e}'
    except Exception as e:
        logger.error('Erreur OCR: %s', e)
        return None, str(e)
