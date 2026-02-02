"""
Validateur principal des logs - Data Officer
"""

import json
import os
from datetime import datetime
from pathlib import Path

def validate_log():
    """Valide le fichier de logs experiment_data.json"""
    
    logs_path = Path(__file__).parent.parent.parent / "logs" / "experiment_data.json"
    
    print("=" * 60)
    print(" VALIDATION DES LOGS - Data Officer")
    print("=" * 60)
    
    # 1. Vérifier l'existence
    if not logs_path.exists():
        print(" ERREUR: Fichier experiment_data.json introuvable")
        print(f"   Chemin: {logs_path}")
        return False
    
    if logs_path.stat().st_size == 0:
        print(" ERREUR: Fichier vide")
        return False
    
    try:
        # 2. Charger le JSON
        with open(logs_path, 'r', encoding='utf-8') as f:
            logs_data = json.load(f)
        
        print(f" Fichier trouvé: {logs_path}")
        print(f" Format JSON valide")
        
        # 3. Vérifier que c'est une liste
        if not isinstance(logs_data, list):
            print(" ERREUR: Doit être un tableau (list) JSON")
            return False
        
        print(f" Nombre d'entrées: {len(logs_data)}")
        
        # 4. Vérifier chaque entrée
        required_fields = ['agent', 'model', 'action', 'timestamp', 'details', 'status']
        required_details = ['input_prompt', 'output_response']
        
        errors = []
        warnings = []
        
        for i, entry in enumerate(logs_data):
            # Champs obligatoires
            for field in required_fields:
                if field not in entry:
                    errors.append(f"Entrée #{i}: '{field}' manquant")
            
            # Détails obligatoires
            if 'details' in entry:
                for detail in required_details:
                    if detail not in entry['details']:
                        errors.append(f"Entrée #{i}: Détail '{detail}' manquant")
            
            # Vérifications de qualité
            if 'details' in entry:
                details = entry['details']
                
                # Longueur des prompts
                if 'input_prompt' in details:
                    prompt_len = len(str(details['input_prompt']))
                    if prompt_len < 10:
                        warnings.append(f"Entrée #{i}: Prompt très court ({prompt_len} chars)")
                
                # Longueur des réponses
                if 'output_response' in details:
                    response_len = len(str(details['output_response']))
                    if response_len < 10:
                        warnings.append(f"Entrée #{i}: Réponse très courte ({response_len} chars)")
        
        # 5. Afficher les résultats
        if errors:
            print("\n ERREURS CRITIQUES:")
            for error in errors[:5]:
                print(f"   - {error}")
            if len(errors) > 5:
                print(f"   ... et {len(errors) - 5} erreurs supplémentaires")
        else:
            print("\n Aucune erreur critique")
        
        if warnings:
            print("\n AVERTISSEMENTS:")
            for warning in warnings[:3]:
                print(f"   - {warning}")
            if len(warnings) > 3:
                print(f"   ... et {len(warnings) - 3} avertissements supplémentaires")
        
        # 6. Statistiques
        if logs_data:
            print("\n STATISTIQUES:")
            
            agents = {}
            actions = {}
            statuses = {}
            
            for entry in logs_data:
                agent = entry.get('agent_name', 'UNKNOWN')
                action = entry.get('action', 'UNKNOWN')
                status = entry.get('status', 'UNKNOWN')
                
                agents[agent] = agents.get(agent, 0) + 1
                actions[action] = actions.get(action, 0) + 1
                statuses[status] = statuses.get(status, 0) + 1
            
            print("   Agents:")
            for agent, count in agents.items():
                print(f"     - {agent}: {count}")
            
            print("\n   Actions:")
            for action, count in actions.items():
                print(f"     - {action}: {count}")
        
        print("\n" + "=" * 60)
        
        if not errors:
            print(" VALIDATION RÉUSSIE - Fichier de logs conforme")
            return True
        else:
            print(" VALIDATION ÉCHOUÉE - Corrections nécessaires")
            return False
            
    except json.JSONDecodeError as e:
        print(f" ERREUR JSON: {e}")
        return False
    except Exception as e:
        print(f" ERREUR: {e}")
        return False

def backup_logs():
    """Crée une sauvegarde des logs"""
    logs_path = Path(__file__).parent.parent.parent / "logs" / "experiment_data.json"
    
    if logs_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = logs_path.parent / f"experiment_data_backup_{timestamp}.json"
        
        import shutil
        shutil.copy2(logs_path, backup_path)
        print(f" Sauvegarde créée: {backup_path.name}")
        return backup_path
    
    return None

if __name__ == "__main__":
    # Sauvegarde avant validation
    backup_logs()
    
    # Validation
    is_valid = validate_log()
    
    if not is_valid:
        print("\n ACTION REQUISE: Corriger les erreurs!")
        exit(1)