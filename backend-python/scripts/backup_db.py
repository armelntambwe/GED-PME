# ============================================
# scripts/backup_db.py - Sauvegarde de la base MySQL
# ============================================
import os
import datetime
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def backup_database():
    """Sauvegarde la base de données MySQL"""
    
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{backup_dir}/ged_pme_{date}.sql"
    
    mysqldump_path = r"C:\xampp\mysql\bin\mysqldump.exe"
    
    # Gestion du mot de passe
    if Config.MYSQL_PASSWORD:
        cmd = f'"{mysqldump_path}" -h {Config.MYSQL_HOST} -u {Config.MYSQL_USER} -p{Config.MYSQL_PASSWORD} {Config.MYSQL_DB} > "{filename}"'
    else:
        cmd = f'"{mysqldump_path}" -h {Config.MYSQL_HOST} -u {Config.MYSQL_USER} {Config.MYSQL_DB} > "{filename}"'
    
    print(f"[BACKUP] Exécution: {cmd}")  # ← Sans émoji
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"[OK] Base sauvegardée: {filename}")  # ← Sans émoji
        return filename
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Sauvegarde base: {e}")  # ← Sans émoji
        return None

if __name__ == "__main__":
    backup_database()