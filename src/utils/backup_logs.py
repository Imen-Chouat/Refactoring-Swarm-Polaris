"""
Système de sauvegarde des logs - Data Officer
"""

import shutil
from datetime import datetime
from pathlib import Path

def backup_experiment_data():
    """Crée une sauvegarde du fichier de logs"""
    
    logs_path = Path(__file__).parent.parent.parent / "logs" / "experiment_data.json"
    
    if not logs_path.exists():
        print("❌ Fichier source introuvable")
        return None
    
    # Créer le dossier de backup s'il n'existe pas
    backup_dir = logs_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Nom du fichier de backup avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"experiment_data_{timestamp}.json"
    backup_path = backup_dir / backup_name
    
    # Copie
    try:
        shutil.copy2(logs_path, backup_path)
        print(f"✅ Sauvegarde créée: {backup_name}")
        return backup_path
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return None

def list_backups():
    """Liste toutes les sauvegardes disponibles"""
    
    backup_dir = Path(__file__).parent.parent.parent / "logs" / "backups"
    
    if not backup_dir.exists():
        print("📁 Aucune sauvegarde trouvée")
        return []
    
    backups = list(backup_dir.glob("experiment_data_*.json"))
    backups.sort(reverse=True)  # Plus récent en premier
    
    print("📁 SAUVEGARDES DISPONIBLES:")
    for i, backup in enumerate(backups[:10]):  # 10 plus récentes
        size_mb = backup.stat().st_size / 1024 / 1024
        print(f"   {i+1}. {backup.name} ({size_mb:.2f} MB)")
    
    return backups

def restore_backup(backup_number=1):
    """Restaure une sauvegarde"""
    
    backups = list_backups()
    
    if not backups:
        print("❌ Aucune sauvegarde à restaurer")
        return False
    
    if backup_number < 1 or backup_number > len(backups):
        print(f"❌ Numéro invalide. Choisissez entre 1 et {len(backups)}")
        return False
    
    backup_to_restore = backups[backup_number - 1]
    destination = backup_to_restore.parent.parent / "experiment_data.json"
    
    try:
        # Sauvegarde de l'actuel d'abord
        current_backup = backup_experiment_data()
        if current_backup:
            print(f"📁 Sauvegarde actuelle: {current_backup.name}")
        
        # Restauration
        shutil.copy2(backup_to_restore, destination)
        print(f"✅ Restauré: {backup_to_restore.name}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur restauration: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            backup_experiment_data()
        elif command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(int(sys.argv[2]))
        else:
            print("Usage: python backup_logs.py [backup|list|restore <num>]")
    else:
        # Par défaut: faire une sauvegarde
        backup_experiment_data()