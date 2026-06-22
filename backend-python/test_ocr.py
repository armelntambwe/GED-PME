# test_ocr.py - À placer dans backend-python/
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Tester avec une image de test
try:
    # Si tu as une image test.jpg, décommente :
    # text = pytesseract.image_to_string(Image.open('test.jpg'), lang='fra+eng')
    # print(text)
    print("✅ Tesseract est fonctionnel")
except Exception as e:
    print(f"❌ Erreur : {e}")
    