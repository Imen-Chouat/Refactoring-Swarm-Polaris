"""
Vérification spécifique des logs de l'Auditor Agent - Data Officer
Compatible avec vos logs qui utilisent 'agent_name' et 'model_used'
"""

import json
import os
from pathlib import Path
from datetime import datetime

def check_auditor_logs():
    """Vérifie que l'Auditor Agent loggue correctement"""
    
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    LOG_FILE = project_root / "logs" / "experiment_data.json"
    
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION AUDITOR AGENT - Data Officer")
    print("="*60)
    
    # 1. Vérifier l'existence du fichier
    if not LOG_FILE.exists():
        print("❌ ERREUR: Fichier experiment_data.json introuvable")
        print(f"   Chemin: {LOG_FILE}")
        return False
    
    if LOG_FILE.stat().st_size == 0:
        print("❌ ERREUR: Fichier vide - Aucun log enregistré")
        return False
    
    try:
        # 2. Charger les logs
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        print(f"📊 Logs totaux: {len(logs)} entrées")
        
        # CORRIGÉ: Vos logs utilisent 'agent_name', pas 'agent'
        # Chercher l'Auditor dans le champ 'agent_name'
        auditor_names = ['Auditor_Agent', 'Auditor', 'auditor_agent', 'auditor', 'AuditorAgent']
        auditor_logs = []
        
        for log in logs:
            # CORRIGÉ: Chercher d'abord 'agent_name', puis 'agent' comme fallback
            agent = log.get('agent_name', log.get('agent', ''))
            if any(name.lower() == agent.lower() for name in auditor_names):
                auditor_logs.append(log)
        
        print(f"📊 Logs Auditor: {len(auditor_logs)} entrées")
        
        if not auditor_logs:
            print("\n❌ CRITIQUE: Aucun log Auditor trouvé!")
            print("   Vos logs utilisent le champ 'agent_name'")
            print("   Vérifiez que votre AuditorAgent appelle log_experiment() avec:")
            print("   - agent_name='Auditor_Agent'")
            print("   - model_used='nom-du-modèle'")
            print("   - details avec 'input_prompt' et 'output_response'")
            return False
        
        # 3. Vérifier la dernière entrée
        last_log = auditor_logs[-1]
        details = last_log.get('details', {})
        
        print(f"\n📝 DERNIÈRE ENTRÉE:")
        print(f"   Agent: {last_log.get('agent_name', last_log.get('agent', 'N/A'))}") 
        print(f"   Modèle: {last_log.get('model_used', last_log.get('model', 'N/A'))}")   
        print(f"   Action: {last_log.get('action', 'N/A')}")
        print(f"   Status: {last_log.get('status', 'N/A')}")
        print(f"   Timestamp: {last_log.get('timestamp', 'N/A')}")
        
        # 4. Vérifier les champs obligatoires
        print("\n✅ VÉRIFICATION CHAMPS OBLIGATOIRES:")
        
        mandatory_fields = {'input_prompt': False, 'output_response': False}
        
        if 'input_prompt' in details:
            mandatory_fields['input_prompt'] = True
            input_len = len(str(details['input_prompt']))
            print(f"   ✅ input_prompt: présent ({input_len} caractères)")
        else:
            print("   ❌ input_prompt: MANQUANT")
        
        if 'output_response' in details:
            mandatory_fields['output_response'] = True
            output_len = len(str(details['output_response']))
            print(f"   ✅ output_response: présent ({output_len} caractères)")
        else:
            print("   ❌ output_response: MANQUANT")
        
        # 5. Statistiques détaillées
        print("\n📈 STATISTIQUES DÉTAILLÉES:")
        
        actions = {}
        for log in auditor_logs:
            action = log.get('action', 'UNKNOWN')
            actions[action] = actions.get(action, 0) + 1
        
        for action, count in actions.items():
            print(f"   - {action}: {count} entrées")
        
        # 6. Qualité des logs
        print("\n🎯 QUALITÉ DES LOGS:")
        good_logs = 0
        problematic_logs = []
        
        for i, log in enumerate(auditor_logs):
            details = log.get('details', {})
            has_input = 'input_prompt' in details and len(str(details['input_prompt'])) > 10
            has_output = 'output_response' in details and len(str(details['output_response'])) > 10
            
            if has_input and has_output:
                good_logs += 1
            else:
                problematic_logs.append(i)
                if len(problematic_logs) <= 3:  # Afficher seulement 3 problèmes
                    issues = []
                    if 'input_prompt' not in details: issues.append("no input")
                    elif len(str(details['input_prompt'])) <= 10: issues.append("short input")
                    if 'output_response' not in details: issues.append("no output")
                    elif len(str(details['output_response'])) <= 10: issues.append("short output")
                    print(f"   ⚠️  Entrée #{i}: {', '.join(issues)}")
        
        quality = (good_logs / len(auditor_logs)) * 100 if auditor_logs else 0
        print(f"   ✅ Logs valides: {good_logs}/{len(auditor_logs)} ({quality:.1f}%)")
        
        # 7. Vérification spécifique à l'Auditor
        print("\n🔍 VÉRIFICATION SPÉCIFIQUE AUDITOR:")
        
        if auditor_logs:
            # Vérifier que l'Auditor fait bien de l'ANALYSIS
            analysis_logs = [log for log in auditor_logs if 'ANALYSIS' in log.get('action', '')]
            print(f"   - Logs d'ANALYSIS: {len(analysis_logs)}/{len(auditor_logs)}")
            
            # Vérifier les champs spécifiques à l'Auditor
            sample_log = auditor_logs[0]
            sample_details = sample_log.get('details', {})
            
            auditor_specific = ['issues_found', 'file_analyzed', 'analysis_type', 'code_quality']
            found_fields = [field for field in auditor_specific if field in sample_details]
            if found_fields:
                print(f"   - Champs spécifiques Auditor: {', '.join(found_fields)}")
            else:
                print(f"   - Aucun champ spécifique Auditor trouvé")
        
        # 8. Vérification de la compatibilité
        print("\n🔧 VÉRIFICATION COMPATIBILITÉ:")
        if auditor_logs:
            sample_log = auditor_logs[0]
            print(f"   Champs utilisés dans les logs:")
            print(f"   - 'agent_name': {'✅' if 'agent_name' in sample_log else '❌'}")
            print(f"   - 'model_used': {'✅' if 'model_used' in sample_log else '❌'}")
            print(f"   - 'agent': {'⚠️' if 'agent' in sample_log else '✅'}")
            print(f"   - 'model': {'⚠️' if 'model' in sample_log else '✅'}")
            print("   💡 Vos logs utilisent 'agent_name' et 'model_used'")
        
        print("\n" + "="*60)
        
        # Critères de validation (adaptés à vos logs)
        if all(mandatory_fields.values()) and quality > 70:
            print("✅ AUDITOR AGENT - LOGGING VALIDÉ")
            print("   Compatible avec vos logs (agent_name/model_used)")
            return True
        elif all(mandatory_fields.values()) and quality > 50:
            print("⚠️  AUDITOR AGENT - LOGGING ACCEPTABLE")
            print("   Qualité moyenne mais champs obligatoires présents")
            return True
        else:
            print("❌ AUDITOR AGENT - PROBLÈMES DÉTECTÉS")
            return False
            
    except json.JSONDecodeError:
        print("❌ ERREUR: Fichier JSON invalide")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = check_auditor_logs()
    exit(0 if success else 1)