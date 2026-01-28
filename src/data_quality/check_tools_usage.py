#!/usr/bin/env python3
"""
Vérifie l'utilisation des outils dans les logs
Data Officer - Vérification indirecte
"""
import json
import os
import re

def check_tools_in_logs():
    """Vérifie si les outils sont mentionnés dans les logs"""
    
    log_file = "logs/experiment_data.json"
    
    if not os.path.exists(log_file):
        print("❌ Aucun fichier de logs")
        return False
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except:
        print("❌ JSON invalide")
        return False
    
    # Outils à vérifier (ceux qui devraient être utilisés)
    expected_tools = {
        "file_tools": ["read_file", "write_file"],
        "pylint_tool": ["run_pylint"],
        "pytest_tool": ["run_pytest"]
    }
    
    print("🔧 VÉRIFICATION DE L'UTILISATION DES OUTILS")
    print("=" * 50)
    
    tool_mentions = {tool: 0 for tools in expected_tools.values() for tool in tools}
    
    # Analyser chaque log
    for log in logs:
        details = log.get('details', {})
        input_prompt = details.get('input_prompt', '')
        output_response = details.get('output_response', '')
        
        # Chercher des mentions d'outils dans les prompts/réponses
        combined_text = f"{input_prompt} {output_response}".lower()
        
        for tool_name in tool_mentions.keys():
            if tool_name.lower() in combined_text:
                tool_mentions[tool_name] += 1
    
    # Afficher les résultats
    all_used = True
    
    for category, tools in expected_tools.items():
        print(f"\n{category.upper()}:")
        for tool in tools:
            count = tool_mentions[tool]
            if count > 0:
                print(f"  ✅ {tool}: utilisé {count} fois")
            else:
                print(f"  ⚠️  {tool}: JAMAIS mentionné")
                all_used = False
    
    # Vérifications spécifiques
    print("\n📋 VÉRIFICATIONS SPÉCIFIQUES:")
    
    # 1. Les agents écrivent-ils des fichiers ?
    if tool_mentions["write_file"] == 0:
        print("  ❌ write_file jamais utilisé - Le Fixer n'écrit pas de fichiers ?")
    
    # 2. L'auditor utilise-t-il pylint ?
    if tool_mentions["run_pylint"] == 0:
        print("  ❌ run_pylint jamais utilisé - L'Auditor ne fait pas d'analyse ?")
    
    # 3. Le judge utilise-t-il pytest ?
    if tool_mentions["run_pytest"] == 0:
        print("  ❌ run_pytest jamais utilisé - Le Judge ne fait pas de tests ?")
    
    print("=" * 50)
    
    if all_used:
        print("✅ Tous les outils semblent être utilisés")
    else:
        print("⚠️  Certains outils ne semblent pas utilisés")
    
    return all_used

if __name__ == "__main__":
    check_tools_in_logs()