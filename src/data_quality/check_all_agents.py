import json
from pathlib import Path
from datetime import datetime

def check_all_agents_logs():
    """Vérifie que TOUS les agents loggent correctement"""
    
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    LOG_FILE = project_root / "logs" / "experiment_data.json"
    
    print("\n" + "="*70)
    print("📊 VÉRIFICATION COMPLÈTE - Data Officer")
    print("(Compatible avec vos logs qui utilisent 'agent_name' et 'model_used')")
    print("="*70)
    
    # 1. Vérifications basiques
    if not LOG_FILE.exists():
        print("❌ ERREUR CRITIQUE: Fichier experiment_data.json introuvable")
        print("   NOTE: Qualité des données = 0/30")
        return False
    
    try:
        file_size = LOG_FILE.stat().st_size
        if file_size == 0:
            print("❌ ERREUR: Fichier vide")
            return False
        
        print(f"✅ Fichier trouvé: {file_size} octets")
        
        # 2. Chargement et validation JSON
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        if not isinstance(logs, list):
            print("❌ ERREUR: Le fichier doit contenir un tableau JSON")
            return False
        
        print(f"✅ Format JSON valide: {len(logs)} entrées")
        
        if len(logs) < 5:
            print(f"⚠️  AVERTISSEMENT: Peu d'entrées ({len(logs)})")
            print("   Recommandé: au moins 20 entrées pour la validation")
        
        # 3. Analyse par agent - CORRIGÉ: VOS LOGS utilisent 'agent_name'
        print("\n" + "="*70)
        print("👥 RÉPARTITION PAR AGENT (champ 'agent_name'):")
        print("="*70)
        
        agents = {}
        for log in logs:
            # CORRIGÉ: Vos logs utilisent 'agent_name', pas 'agent'
            agent = log.get('agent_name', log.get('agent', 'UNKNOWN'))
            agents[agent] = agents.get(agent, 0) + 1
        
        if not agents:
            print("   ❌ Aucun agent trouvé dans les logs")
            print("   Vérifiez que vos agents appellent bien log_experiment()")
            return False
        
        for agent, count in sorted(agents.items(), key=lambda x: x[1], reverse=True):
            print(f"   {agent:20} : {count:3} entrées")
        
        # 4. Vérification des champs obligatoires
        print("\n" + "="*70)
        print("✅ VÉRIFICATION CHAMPS OBLIGATOIRES:")
        print("(Dans 'details': input_prompt et output_response)")
        print("="*70)
        
        missing_input = 0
        missing_output = 0
        short_responses = 0
        
        for i, log in enumerate(logs):
            details = log.get('details', {})
            
            # Champs obligatoires
            if 'input_prompt' not in details:
                missing_input += 1
                if missing_input <= 2:  # Afficher seulement 2 exemples
                    print(f"   ❌ Entrée #{i}: 'input_prompt' manquant")
            
            if 'output_response' not in details:
                missing_output += 1
                if missing_output <= 2:
                    print(f"   ❌ Entrée #{i}: 'output_response' manquant")
            
            # Qualité des réponses
            if 'output_response' in details:
                response = str(details['output_response'])
                if len(response) < 10:
                    short_responses += 1
        
        total_logs = len(logs)
        
        print(f"\n   input_prompt manquant     : {missing_input}/{total_logs}")
        print(f"   output_response manquant : {missing_output}/{total_logs}")
        print(f"   Réponses trop courtes    : {short_responses}/{total_logs}")
        
        # 5. Analyse par type d'action
        print("\n" + "="*70)
        print("🎯 RÉPARTITION PAR TYPE D'ACTION:")
        print("="*70)
        
        actions = {}
        for log in logs:
            action = log.get('action', 'UNKNOWN')
            actions[action] = actions.get(action, 0) + 1
        
        for action, count in actions.items():
            print(f"   {action:15} : {count:3}")
        
        # 6. Vérifier la présence des 3 agents principaux
        print("\n" + "="*70)
        print("👥 PRÉSENCE DES 3 AGENTS PRINCIPAUX:")
        print("="*70)
        
        expected_agents = ['Auditor', 'Fixer', 'Judge', 'Auditor_Agent', 'Fixer_Agent', 'JudgeAgent']
        found_agents = []
        
        for agent_name in agents.keys():
            for expected in expected_agents:
                if expected.lower() in str(agent_name).lower():
                    found_agents.append(expected)
                    break
        
        print("   Agents attendus: Auditor, Fixer, Judge")
        print(f"   Agents trouvés : {', '.join(set(found_agents)) if found_agents else 'AUCUN'}")
        
        if len(set(found_agents)) >= 3:
            print("   ✅ Tous les agents principaux sont présents")
        elif len(set(found_agents)) >= 2:
            print("   ⚠️  Seulement 2 agents sur 3 trouvés")
        else:
            print("   ❌ Moins de 2 agents trouvés")
        
        # 7. Score final (adapté à vos logs)
        print("\n" + "="*70)
        print("📈 SCORE FINAL - DATA QUALITY:")
        print("(Adapté à vos logs avec 'agent_name' et 'model_used')")
        print("="*70)
        
        # Calcul du score (sur 100)
        score = 100
        
        # Pénalités pour champs manquants
        if missing_input > 0:
            penalty = (missing_input / total_logs) * 40
            score -= penalty
            print(f"   - input_prompt manquant : -{penalty:.1f} points")
        
        if missing_output > 0:
            penalty = (missing_output / total_logs) * 40
            score -= penalty
            print(f"   - output_response manquant : -{penalty:.1f} points")
        
        if total_logs < 10:
            penalty = (10 - total_logs) * 3
            score -= penalty
            print(f"   - Logs insuffisants : -{penalty:.1f} points")
        
        # Bonus
        if len(set(found_agents)) >= 3:
            score += 15
            print(f"   + 3 agents ou plus : +15 points")
        
        if total_logs >= 20:
            score += 10
            print(f"   + Logs nombreux ({total_logs}) : +10 points")
        
        # Limiter le score entre 0 et 100
        score = max(0, min(100, score))
        
        print(f"\n   📊 SCORE FINAL : {score:.1f}/100")
        
        # 8. Recommandations spécifiques
        print("\n" + "="*70)
        print("💡 RECOMMANDATIONS (spécifiques à vos logs):")
        print("="*70)
        
        if missing_input > 0 or missing_output > 0:
            print("   ❌ CORRIGER URGENCE: Champs obligatoires manquants")
            print("      Vérifiez que tous les appels à log_experiment() ont:")
            print("      - details['input_prompt'] = prompt exact")
            print("      - details['output_response'] = réponse exacte")
        
        if total_logs < 20:
            print(f"   📈 AJOUTER DES LOGS: Seulement {total_logs} entrées")
            print("      Exécutez vos agents sur plus de fichiers")
        
        if len(set(found_agents)) < 3:
            print(f"   👥 AGENTS MANQUANTS: {len(set(found_agents))}/3 agents")
            print("      Vérifiez que tous les agents appellent log_experiment()")
        
        # Vérification de la structure réelle de vos logs
        print("\n🔧 VÉRIFICATION STRUCTURE DE VOS LOGS:")
        if logs:
            sample_log = logs[0]
            print(f"   Structure du premier log:")
            print(f"   - Utilise 'agent_name': {'✅' if 'agent_name' in sample_log else '❌'}")
            print(f"   - Utilise 'model_used': {'✅' if 'model_used' in sample_log else '❌'}")
            print(f"   - Utilise 'agent': {'⚠️' if 'agent' in sample_log else '✅'}")
            print("   💡 Vos logs utilisent 'agent_name' et 'model_used'")
            
            # Afficher tous les champs pour vérification
            print(f"\n   📋 Tous les champs du log:")
            for key in sample_log.keys():
                print(f"   - '{key}'")
        
        print("\n" + "="*70)
        
        # Critère de succès (adapté à vos logs)
        if score >= 60 and missing_input == 0 and missing_output == 0:
            print("✅ QUALITÉ DES DONNÉES VALIDÉE")
            print("   Compatible avec vos logs (agent_name/model_used)")
            print("   Prêt pour la soumission!")
            return True
        elif score >= 40:
            print("⚠️  QUALITÉ DES DONNÉES MOYENNE")
            print("   Améliorations recommandées avant soumission")
            return True  # Acceptable
        else:
            print("❌ QUALITÉ DES DONNÉES INSUFFISANTE")
            print("   Corrections nécessaires avant soumission")
            return False
            
    except json.JSONDecodeError:
        print("❌ ERREUR: Fichier JSON invalide ou corrompu")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = check_all_agents_logs()
    exit(0 if success else 1)