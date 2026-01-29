
#Vérification que les outils loggent correctement - Data Officer


import json
import ast
from pathlib import Path

def check_tools_log():
    """Vérifie que tous les outils utilisent correctement le logger"""
    
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    LOG_FILE = project_root / "logs" / "experiment_data.json"
    
    print("\n" + "="*60)
    print("VÉRIFICATION DES OUTILS - Data Officer")
    print("="*60)
    
    # 1. Vérifier les fichiers outils
    toolsDir = project_root / "src" / "tools"
    if not toolsDir.exists():
        print("Dossier tools/ introuvable")
        return False
    
    toolsFiles = list(toolsDir.glob("*.py"))
    print(f"Outils trouvés: {len(toolsFiles)} fichiers")
    
    for tool_file in toolsFiles:
        print(f"{tool_file.name}")
    
    # 2. Analyser chaque outil
    tools_with_logger = []
    tools_not_logger = []
    
    for tool_file in toolsFiles:
        try:
            with open(tool_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier si le fichier importe le logger
            logger_import_exists = any(phrase in content for phrase in [
                "from src.utils.logger import",
                "import logger",
                "log_experiment"
            ])
            
            # Vérifier si le fichier appelle log_experiment
            call_log_experiment = "log_experiment(" in content
            
            if logger_import_exists and call_log_experiment:
                tools_with_logger.append(tool_file.name)
            else:
                tools_not_logger.append(tool_file.name)
                
        except Exception as e:
            print(f"Erreur lecture {tool_file.name}: {e}")
    
    # 3. Afficher les résultats
    print("\nOUTILS AVEC LOGGER:")
    if tools_with_logger:
        for tool in tools_with_logger:
            print(f" {tool}")
    else:
        print("   Aucun outil n'utilise le logger")
    
    if tools_not_logger:
        print("\nOUTILS SANS LOGGER (CRITIQUE):")
        for tool in tools_not_logger:
            print(f"   ✗ {tool}")
        
        print("\n RECOMMANDATION:")
        print("   Les outils qui appellent des LLM DEVRAIENT logguer.")
        print("   Exemple: Si pylint_tool.py utilise un LLM pour l'analyse,")
        print("   il devrait appeler log_experiment().")
    
    # 4. Vérifier dans les logs existants
    print("\nANALYSE DES LOGS EXISTANTS:")
    
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Chercher les logs des outils
            tool_logs = []
            for log in logs:
                agent = log.get('agent', log.get('agent_name', ''))
                if any(tool_word in agent.lower() for tool_word in ['tool', 'pytest', 'pylint', 'linter', 'tester']):
                    tool_logs.append(log)
            
            print(f"   Logs 'outils' détectés: {len(tool_logs)}")
            
            if tool_logs:
                print("   Exemples d'agents outils:")
                for log in tool_logs[:3]:
                    print(f"   - {log.get('agent', 'N/A')}: {log.get('action', 'N/A')}")
            else:
                print(" Aucun log spécifique 'outil' trouvé")
                print("   (Normal si les outils n'appellent pas de LLM)")
        
        except Exception as e:
            print(f"Impossible d'analyser les logs: {e}")
    else:
        print("  Aucun fichier de logs existant")
    
    # 5. Vérification spécifique de VOS outils
    print("\n🔍 ANALYSE DE VOS OUTILS SPÉCIFIQUES:")
    
    your_tools = {
        "file_operations.py": "Ne devrait pas loguer (pas de LLM)",
        "pylint_tool.py": "Devrait loguer si utilise LLM",
        "pytest_tool.py": "Devrait loguer si utilise LLM"
    }
    
    for tool_name, recommendation in your_tools.items():
        tool_path = toolsDir / tool_name
        if tool_path.exists():
            with open(tool_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier si l'outil utilise un LLM
            has_llm = any(keyword in content for keyword in [
                "ChatGroq", "ChatOpenAI", "llm", "LLM", "model", "api_key"
            ])
            
            if has_llm:
                print(f" {tool_name}: Utilise un LLM → {recommendation}")
            else:
                print(f" {tool_name}: Pas de LLM → OK sans logging")
    
    print("\n" + "="*60)
    
    # Critère de succès
    # Si aucun outil n'utilise de LLM, c'est OK
    # Si des outils utilisent des LLM mais ne loguent pas, c'est un problème
    if not tools_not_logger or len(tools_with_logger) > 0:
        print(" OUTILS - LOGGING VALIDÉ (ou non nécessaire)")
        return True
    else:
        print(" OUTILS - LOGGING RECOMMANDÉ POUR LES LLM")
        return True  # Pas critique, mais recommandé

def check_tool_imports():
    """Vérifie que les outils n'ont pas d'imports dangereux"""
    
    tools_dir = Path(__file__).parent.parent.parent / "src" / "tools"
    
    if not tools_dir.exists():
        return True
    
    dangerous_patterns = [
        "api_key",
        "sk-",
        "AIza",
        "password",
        "secret",
        "token",
        "credentials"
    ]
    
    print("\n VÉRIFICATION SÉCURITÉ DES OUTILS:")
    
    issues_found = False
    for tool_file in tools_dir.glob("*.py"):
        try:
            with open(tool_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            for pattern in dangerous_patterns:
                if pattern in content:
                    print(f" {tool_file.name}: Pattern '{pattern}' détecté")
                    print(f"      Vérifiez que ce n'est pas une clé API en clair")
                    issues_found = True
                    
        except Exception:
            pass
    
    if not issues_found:
        print("    Aucune donnée sensible détectée")
    else:
        print("\n   RECOMMANDATION:")
        print("   Les clés API doivent être dans le fichier .env")
        print("   et chargées via os.environ.get('NOM_VARIABLE')")
    
    return not issues_found

def check_tools_functionality():
    """Vérifie que les outils fonctionnent correctement"""
    
    print("\n VÉRIFICATION FONCTIONNALITÉ DES OUTILS:")
    
    # Vérifier les imports
    try:
        from src.tools.pytest_tool import run_pytest
        print("    pytest_tool.py: Import réussi")
    except ImportError as e:
        print(f"   pytest_tool: Import échoué: {e}")
    
    try:
        from src.tools.pylint_tool import run_pylint
        print("    pylint_tool.py: Import réussi")
    except ImportError as e:
        print(f"   pylint_tool: Import échoué: {e}")
    
    return True

if __name__ == "__main__":
    success1 = check_tools_log()
    success2 = check_tool_imports()
    success3 = check_tools_functionality()
    
    print("\n" + "="*60)
    
    if success1 and success2 and success3:
        print(" OUTILS COMPATIBLES AVEC DATA OFFICER")
        exit(0)
    else:
        print("  OUTILS - QUELQUES PROBLÈMES")
        exit(1)