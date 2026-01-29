
#Vérification spécifique des logs du Fixer Agent - Data Officer


import json
from pathlib import Path

def check_fixer_logs():
    """Vérifie que le Fixer Agent loggue correctement"""
    
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    LOG_FILE = project_root / "logs" / "experiment_data.json"
    
    print("\n" + "="*60)
    print("VÉRIFICATION FIXER AGENT - Data Officer")
    print("="*60)
    
    if not LOG_FILE.exists():
        print("Fichier de logs introuvable")
        return False
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
    
        fixer_names = ['Fixer_Agent', 'Fixer', 'fixer_agent', 'fixer', 'FixerAgent']
        fixer_logs = []
        
        for log in logs:
            agent = log.get('agent_name', log.get('agent', ''))
            if any(name.lower() == agent.lower() for name in fixer_names):
                fixer_logs.append(log)
        
        print(f" Logs totaux: {len(logs)}")
        print(f" Logs Fixer: {len(fixer_logs)}")
        
        if not fixer_logs:
            print("\n Aucun log Fixer trouvé")
            print("   Vérifiez que votre FixerAgent appelle log_experiment() avec agent_name='Fixer_Agent'")
            print("   (Votre logger le stockera comme 'agent': 'Fixer_Agent')")
            return False
        
        # Analyse détaillée
        print("\nANALYSE DÉTAILLÉE DES LOGS FIXER:")
        
        fix_actions = 0
        generation_actions = 0
        errors = 0
        success = 0
        
        for log in fixer_logs:
            action = log.get('action', '')
            status = log.get('status', '')
            
            if 'FIX' in action or action == 'FIX':
                fix_actions += 1
            if 'GENERATION' in action or action == 'GENERATION':
                generation_actions += 1
            if status == 'ERROR':
                errors += 1
            elif status == 'SUCCESS':
                success += 1
        
        print(f"   Actions FIX: {fix_actions}")
        print(f"   Actions GENERATION: {generation_actions}")
        print(f"   Statut SUCCESS: {success}")
        print(f"   Statut ERROR: {errors}")
        
        # Vérifier les champs obligatoires
        print("\nVÉRIFICATION CHAMPS OBLIGATOIRES:")
        
        mandatory_ok = 0
        problematic_logs = []
        
        for i, log in enumerate(fixer_logs[:10]):  # Vérifier les 10 premiers
            details = log.get('details', {})
            
            has_input = 'input_prompt' in details
            has_output = 'output_response' in details
            
            if has_input and has_output:
                mandatory_ok += 1
                
                # Vérifier la qualité
                input_len = len(str(details['input_prompt']))
                output_len = len(str(details['output_response']))
                
                if input_len < 10 or output_len < 10:
                    problematic_logs.append((i, f"trop court (in:{input_len}, out:{output_len})"))
            else:
                missing = []
                if not has_input: missing.append("input_prompt")
                if not has_output: missing.append("output_response")
                problematic_logs.append((i, f"manquant: {', '.join(missing)}"))
        
        print(f"   Logs avec champs obligatoires: {mandatory_ok}/{len(fixer_logs)}")
        
        if problematic_logs:
            print("\n LOGS PROBLÉMATIQUES (premiers 3):")
            for i, problem in problematic_logs[:3]:
                print(f"   - Log #{i}: {problem}")
        
        # Vérifier le contenu spécifique au Fixer
        print("\nCONTENU SPÉCIFIQUE FIXER:")
        
        if fixer_logs:
            last_log = fixer_logs[-1]
            details = last_log.get('details', {})
            
            print(f"   Dernier log Fixer:")
            print(f"   - Agent: {last_log.get('agent_name', last_log.get('agent', 'N/A'))}")
            print(f"   - Action: {last_log.get('action', 'N/A')}")
            print(f"   - Status: {last_log.get('status', 'N/A')}")
            
            # Aperçu du prompt
            if 'input_prompt' in details:
                preview = str(details['input_prompt'])[:80]
                print(f"   - Input preview: {preview}...")
            
            # Vérifier si le Fixer modifie des fichiers
            fixer_specific = ['file_fixed', 'file_modified', 'changes_made', 'fix_description']
            found_specific = [field for field in fixer_specific if field in details]
            if found_specific:
                print(f"   - Champs spécifiques: {', '.join(found_specific)}")
        
        print("\n" + "="*60)
        
        # Critères de validation
        if len(fixer_logs) >= 3 and mandatory_ok >= 3:
            print("FIXER AGENT - LOGGING VALIDÉ")
            print("   Compatible avec votre logger (agent_name/model_used)")
            return True
        elif len(fixer_logs) >= 1 and mandatory_ok >= 1:
            print(" FIXER AGENT - LOGGING ACCEPTABLE")
            print("   Mais pourrait être amélioré")
            return True
        else:
            print("FIXER AGENT - LOGGING INSUFFISANT")
            return False
            
    except json.JSONDecodeError as e:
        print(f"ERREUR JSON: {e}")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = check_fixer_logs()
    exit(0 if success else 1)