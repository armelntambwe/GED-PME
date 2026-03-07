# ============================================
# test_upload_config.py - Test de configuration
# ============================================

from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS
import os

print("=" * 60)
print("🔍 TEST CONFIGURATION UPLOAD - GED-PME")
print("=" * 60)

# Test 1: Dossier uploads
print(f"\n1️⃣ DOSSIER UPLOADS")
print(f"   Chemin : {UPLOAD_FOLDER}")
if os.path.exists(UPLOAD_FOLDER):
    print(f"   ✅ EXISTE - Prêt à recevoir des fichiers")
else:
    print(f"   ❌ N'EXISTE PAS - Crée-le avec: mkdir {UPLOAD_FOLDER}")

# Test 2: Taille maximale
print(f"\n2️⃣ TAILLE MAXIMALE")
print(f"   {MAX_CONTENT_LENGTH} octets")
print(f"   Soit {MAX_CONTENT_LENGTH/1024/1024:.0f} Mo")
print(f"   ✅ OK")

# Test 3: Formats autorisés
print(f"\n3️⃣ FORMATS AUTORISÉS (PHASE 1)")
print(f"   {len(ALLOWED_EXTENSIONS)} formats supportés :")
for ext in sorted(ALLOWED_EXTENSIONS):
    print(f"   • .{ext}")

# Test 4: Fonctions utilitaires
print(f"\n4️⃣ FONCTIONS UTILITAIRES")
try:
    from utils.file_upload import allowed_file, get_file_size, secure_filename_with_path
    print(f"   ✅ Module chargé avec succès")
    
    # Test allowed_file
    test_files = ['doc.pdf', 'image.JPG', 'virus.exe', 'document']
    print(f"\n   Test de validation :")
    for f in test_files:
        result = allowed_file(f)
        status = "✅ AUTORISÉ" if result else "❌ REFUSÉ"
        print(f"   • {f:15} → {status}")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "=" * 60)
print("✅ CONFIGURATION TERMINÉE - Prêt pour la route d'upload !")
print("=" * 60)