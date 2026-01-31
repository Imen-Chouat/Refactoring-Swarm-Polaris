
#Vérification des logs du Judge Agent - Data Officer


import json
from pathlib import Path

def check_judge_logs():
    """Vérifie que le Judge Agent loggue correctement"""
    
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    LOG_FILE = project_root / "logs" / "experiment_data.json"
    
    print("\n" + "="*60)
    print(" VÉRIFICATION JUDGE AGENT - Data Officer")
    print("="*60)
    
    if not LOG_FILE.exists():
        print(" Fichier de logs introuvable")
        return False
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
       
        judge_names = ['JudgeAgent', 'Judge_Agent', 'judge', 'Judge']
        judge_logs = []
        
        for log in logs:
            agent = log.get('agent_name', log.get('agent', ''))
            if any(name.lower() in agent.lower() for name in judge_names):
                judge_logs.append(log)
        
        print(f" Logs totaux: {len(logs)}")
        print(f"Logs Judge: {len(judge_logs)}")
        
        if not judge_logs:
            print("\n Aucun log Judge trouvé")
            print("   Votre JudgeAgent devrait créer des logs avec agent='JudgeAgent'")
            print("   Vérifiez que _log_evaluation() est bien appelé")
            return False
        
        print("\n RÉPARTITION DES ACTIONS:")
        
        action_counts = {}
        for log in judge_logs:
            action = log.get('action', 'UNKNOWN')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action, count in action_counts.items():
            print(f"   - {action}: {count}")
        
        print("\n QUALITÉ DES LOGS :")
        
        good_logs = 0
        problematic_logs = []
        
        for i, log in enumerate(judge_logs):
            details = log.get('details', {})
            
            has_mandatory = 'input_prompt' in details and 'output_response' in details
            
           
            has_test_data = any(key in details for key in [
                'pytest_passed', 'pylint_score', 'tests_generated',
                'file_evaluated', 'errors'
            ])
            
            input_ok = len(str(details.get('input_prompt', ''))) > 10
            output_ok = len(str(details.get('output_response', ''))) > 10
            
            if has_mandatory and has_test_data and input_ok and output_ok:
                good_logs += 1
            else:
                problematic_logs.append(i)
                if len(problematic_logs) <= 3:  
                    issues = []
                    if not has_mandatory: issues.append("champs manquants")
                    if not has_test_data: issues.append("pas données test")
                    if not input_ok: issues.append("input trop court")
                    if not output_ok: issues.append("output trop court")
                    print(f"     Log #{i}: {', '.join(issues)}")
        
        quality = (good_logs / len(judge_logs)) * 100 if judge_logs else 0
        print(f"   Logs complets: {good_logs}/{len(judge_logs)} ({quality:.1f}%)")
        
        print("\n CONTENU DES LOGS JUDGEAGENT:")
        if judge_logs:
            last = judge_logs[-1]
            details = last.get('details', {})
            
            print(f"   Dernière entrée:")
            print(f"   - Agent: {last.get('agent_name', last.get('agent', 'N/A'))}")
            print(f"   - Action: {last.get('action', 'N/A')}")
            print(f"   - Status: {last.get('status', 'N/A')}")
            
            # Vérifier les champs spécifiques du Judge
            if 'pytest_passed' in details:
                print(f"   - Pytest passé: {details['pytest_passed']}")
            if 'pylint_score' in details:
                print(f"   - Score Pylint: {details['pylint_score']}")
            if 'tests_generated' in details:
                print(f"   - Tests générés: {details['tests_generated']}")
            
            # Aperçu du prompt
            input_preview = str(details.get('input_prompt', ''))[:100]
            if input_preview:
                print(f"   - Input preview: {input_preview}...")
        
        # Vérification de la cohérence avec votre code JudgeAgent
        print("\n VÉRIFICATION COHÉRENCE AVEC VOTRE JUDGEAGENT:")
        
        # Votre JudgeAgent utilise ActionType.DEBUG (qui vaut "DEBUG")
        debug_logs = [log for log in judge_logs if log.get('action') == 'DEBUG']
        print(f"   - Logs avec action='DEBUG': {len(debug_logs)} (votre JudgeAgent utilise DEBUG)")
        
        # Votre JudgeAgent envoie ces champs dans details
        expected_fields = ['file_evaluated', 'pytest_passed', 'pylint_score', 'tests_generated']
        if judge_logs:
            details = judge_logs[0].get('details', {})
            for field in expected_fields:
                has_field = field in details
                print(f"   - '{field}' présent: {'PRESENT' if has_field else 'NOT PRESENT'}")
        
        print("\n" + "="*60)
        
        # Critères de validation
        if len(judge_logs) >= 2 and quality > 60:
            print("JUDGE AGENT - LOGGING VALIDÉ")
            print("   Compatible avec votre logger (agent/model)")
            return True
        elif len(judge_logs) >= 1 and quality > 30:
            print(" JUDGE AGENT - LOGGING ACCEPTABLE")
            print("   Mais pourrait être amélioré")
            return True
        else:
            print(" JUDGE AGENT - LOGGING INSUFFISANT")
            return False
            
    except json.JSONDecodeError as e:
        print(f"ERREUR JSON: {e}")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = check_judge_logs()
    exit(0 if success else 1)