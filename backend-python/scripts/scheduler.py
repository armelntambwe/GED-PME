# ============================================
# scripts/scheduler.py - Planificateur de sauvegardes
# GED-PME - Sauvegarde automatique des données
# ============================================

import schedule      # Bibliothèque pour planifier des tâches
import time          # Gestion du temps (secondes, minutes)
import subprocess    # Pour exécuter d'autres scripts Python
import sys           # Pour accéder au chemin de l'interpréteur Python
import os            # Pour les opérations système

# ============================================
# FONCTION DE SAUVEGARDE COMPLÈTE
# ============================================
def backup_all():
    """
    Lance les deux types de sauvegarde (base de données + fichiers)
    Cette fonction est appelée automatiquement par le planificateur
    """
    
    # En-tête de la sauvegarde
    print(f"\n{'='*50}")
    print(f"🔄 Démarrage des sauvegardes - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # ===== SAUVEGARDE DE LA BASE DE DONNÉES =====
    print("\n📦 Sauvegarde de la base...")
    
    # Exécute le script backup_db.py et capture la sortie
    result_db = subprocess.run(
        [sys.executable, "scripts/backup_db.py"],  # Commande: python scripts/backup_db.py
        capture_output=True,                        # Capture stdout et stderr
        text=True                                   # Retourne du texte (pas des bytes)
    )
    
    # Affiche la sortie du script (stdout)
    if result_db.stdout:
        print(result_db.stdout)
    
    # Affiche les erreurs éventuelles (stderr)
    if result_db.stderr:
        print(f"❌ Erreur base: {result_db.stderr}")
    
    # ===== SAUVEGARDE DES FICHIERS UPLOADÉS =====
    print("\n📁 Sauvegarde des fichiers...")
    
    # Exécute le script backup_files.py
    result_files = subprocess.run(
        [sys.executable, "scripts/backup_files.py"],
        capture_output=True,
        text=True
    )
    
    # Affiche la sortie
    if result_files.stdout:
        print(result_files.stdout)
    
    # Affiche les erreurs
    if result_files.stderr:
        print(f"❌ Erreur fichiers: {result_files.stderr}")
    
    # Pied de page
    print(f"\n✅ Sauvegardes terminées - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")


# ============================================
# TEST IMMÉDIAT (POUR VÉRIFICATION)
# ============================================
print("🔧 Exécution d'un test de sauvegarde...")
backup_all()  # Lance une sauvegarde immédiate pour vérifier que tout fonctionne


# ============================================
# PLANIFICATION DES SAUVEGARDES
# ============================================
# Planifie une sauvegarde tous les jours à 2h du matin
# Format: schedule.every().day.at("HH:MM").do(fonction)
schedule.every(5).minutes.do(backup_all)  # Sauvegarde toutes les 5 minutes

# Alternative: sauvegarde toutes les heures (pour test)
# schedule.every().hour.do(backup_all)

# Alternative: sauvegarde toutes les 30 minutes
# schedule.every(30).minutes.do(backup_all)

0
# ============================================
# BOUCLE PRINCIPALE
# ============================================
print("=" * 50)
print("⏰ PLANIFICATEUR DE SAUVEGARDE GED-PME")
print("=" * 50)
print(f"Démarré à: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("Sauvegarde quotidienne programmée à 02:00")
print("Appuyez sur Ctrl+C pour arrêter")
print("=" * 50)

try:
    # Boucle infinie pour vérifier les tâches planifiées
    while True:
        schedule.run_pending()  # Exécute les tâches dont l'heure est arrivée
        time.sleep(60)          # Attend 60 secondes avant de revérifier
        # Note: time.sleep(60) signifie qu'on vérifie toutes les minutes
        # Si on avait mis time.sleep(1), on vérifierait chaque seconde
        # mais cela consommerait plus de CPU inutilement
        
except KeyboardInterrupt:
    # Gestion de l'arrêt par Ctrl+C
    print("\n🛑 Planificateur arrêté")
    print(f"Arrêté à: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("👋 À bientôt !")