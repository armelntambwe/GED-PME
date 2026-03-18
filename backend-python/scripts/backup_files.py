# ============================================
# scripts/backup_files.py - Sauvegarde des fichiers uploadés
# ============================================
import os
import datetime
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import UPLOAD_FOLDER

def backup_files():
    """Sauvegarde le dossier uploads/"""
    
    source_dir = UPLOAD_FOLDER
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    if not os.path.exists(source_dir):
        print(f"[ERREUR] Dossier {source_dir} introuvable")
        return None
    
    date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = f"{backup_dir}/uploads_{date}"
    
    try:
        shutil.copytree(source_dir, dest_dir)
        
        # Calculer la taille totale
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dest_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        print(f"[OK] Fichiers sauvegardés: {dest_dir}")
        print(f"[INFO] Taille: {total_size} octets ({total_size/1024:.2f} Ko)")
        return dest_dir
    except Exception as e:
        print(f"[ERREUR] Sauvegarde fichiers: {e}")
        return None

if __name__ == "__main__":
    backup_files()