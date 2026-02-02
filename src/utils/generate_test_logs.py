"""
Générateur de logs de test - Data Officer
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_test_logs(num_entries=20):
    """Génère des logs de test valides"""
    
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    logs_file = logs_dir / "experiment_data.json"
    
    print("=" * 60)
    print(" GÉNÉRATION DE LOGS DE TEST - Data Officer")
    print("=" * 60)
    
    # Données de test
    agents = ["Auditor_Agent", "Fixer_Agent", "JudgeAgent"]
    models = ["gemini-2.5-flash", "llama-3.3-70b-versatile", "gpt-4o-mini"]
    actions = ["ANALYSIS", "FIX", "GENERATION", "DEBUG"]
    files = ["main.py", "utils.py", "agent.py", "test_file.py"]
    
    # Génération
    logs_data = []
    base_time = datetime.now() - timedelta(hours=2)
    
    for i in range(num_entries):
        timestamp = (base_time + timedelta(minutes=i*5)).isoformat() + "Z"
        
        log = {
            "agent_name": random.choice(agents),
            "model_used": random.choice(models),
            "action": random.choice(actions),
            "timestamp": timestamp,
            "details": {
                "input_prompt": f"Prompt de test #{i+1} - Analyse du code pour amélioration",
                "output_response": f"Réponse de test #{i+1} - J'ai trouvé {random.randint(1,5)} problèmes",
                "file_analyzed": random.choice(files),
                "issues_found": random.randint(1, 5)
            },
            "status": "SUCCESS" if random.random() > 0.1 else "ERROR"
        }
        
        logs_data.append(log)
    
    # Sauvegarde
    with open(logs_file, 'w', encoding='utf-8') as f:
        json.dump(logs_data, f, indent=2, ensure_ascii=False)
    
    print(f" {num_entries} logs générés")
    print(f" Chemin: {logs_file}")
    print("\n Utilisation:")
    print("   1. python src/utils/validate_logs.py")
    print("   2. python src/data_quality/check_all_agents.py")
    
    return logs_file

if __name__ == "__main__":
    generate_test_logs()