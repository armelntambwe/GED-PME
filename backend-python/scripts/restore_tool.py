# ============================================
# scripts/restore_tool.py - Outil de restauration des données
# ============================================
import os
import datetime
import subprocess
import shutil
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def list_backups():
    """Liste les sauvegardes disponibles"""
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        print("❌ Aucun dossier backups trouvé")
        return [], []
    
    # Sauvegardes base
    db_backups = [f for f in os.listdir(backup_dir) if f.startswith('ged_pme_') and f.endswith('.sql')]
    db_backups.sort(reverse=True)
    
    # Sauvegardes fichiers
    file_backups = [d for d in os.listdir(backup_dir) if d.startswith('uploads_')]
    file_backups.sort(reverse=True)
    
    return db_backups, file_backups

def restore_database(backup_file):
    """Restaure la base de données"""
    backup_path = os.path.join('backups', backup_file)
    cmd = f"mysql -h {MYSQL_HOST} -u {MYSQL_USER} -p{MYSQL_PASSWORD} {MYSQL_DB} < {backup_path}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Base restaurée: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur restauration base: {e}")
        return False

def restore_files(backup_dir):
    """Restaure les fichiers uploadés"""
    source_dir = os.path.join('backups', backup_dir)
    dest_dir = 'uploads_restored'
    
    try:
        shutil.copytree(source_dir, dest_dir)
        print(f"✅ Fichiers restaurés dans {dest_dir}")
        print("⚠️ Remplacez manuellement le dossier 'uploads' par ce dossier")
        return True
    except Exception as e:
        print(f"❌ Erreur restauration fichiers: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 OUTIL DE RESTAURATION GED-PME")
    print("=" * 50)
    
    db_backups, file_backups = list_backups()
    
    if db_backups:
        print(f"\n📁 Sauvegardes base disponibles ({len(db_backups)}):")
        for i, b in enumerate(db_backups[:5]):
            print(f"  {i+1}. {b}")
    
    if file_backups:
        print(f"\n📁 Sauvegardes fichiers disponibles ({len(file_backups)}):")
        for i, f in enumerate(file_backups[:5]):
            print(f"  {i+1}. {f}")
    
    print("\nUtilisez restore_database('nom_fichier.sql') et restore_files('nom_dossier')")