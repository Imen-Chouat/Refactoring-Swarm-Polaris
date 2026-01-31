"""
Vérification des prompts - Data Officer
"""

import re
from pathlib import Path

def check_prompts_log():
    """Vérifie la qualité et sécurité des prompts"""
    
    prompts_dir = Path(__file__).parent.parent.parent / "src" / "prompts"
    
    print("\n" + "="*60)
    print(" VÉRIFICATION DES PROMPTS - Data Officer")
    print("="*60)
    
    if not prompts_dir.exists():
        print(" Dossier prompts/ introuvable")
        return False
    
    prompt_files = list(prompts_dir.glob("*.txt")) + list(prompts_dir.glob("*.md"))
    print(f" Prompts trouvés: {len(prompt_files)} fichiers")
    
    if not prompt_files:
        print(" Aucun fichier de prompt trouvé")
        return True  # Pas critique mais étrange
    
    # 1. Vérifier chaque prompt
    issues = []
    warnings = []
    
    for prompt_file in prompt_files:
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_issues = []
            file_warnings = []
            
            # Vérification sécurité
            dangerous_patterns = [
                (r'api_key\s*=', "Variable API_KEY détectée"),
                (r'sk-[a-zA-Z0-9]{20,}', "Clé API OpenAI format"),
                (r'AIza[0-9A-Za-z\-_]{35}', "Clé API Google format"),
                (r'password\s*=', "Mot de passe en clair"),
                (r'secret\s*=', "Secret en clair")
            ]
            
            for pattern, message in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    file_issues.append(f"{message} dans {prompt_file.name}")
            
            # Vérification qualité
            if len(content.strip()) < 50:
                file_warnings.append(f"Prompt très court ({len(content)} caractères)")
            
            if len(content) > 10000:
                file_warnings.append(f"Prompt très long ({len(content)} caractères)")
            
            # Vérifier la structure
            if "ROLE:" not in content and "You are" not in content:
                file_warnings.append("Structure ROLE:/You are manquante")
            
            if "TASK:" not in content and "Your task" not in content:
                file_warnings.append("Structure TASK:/Your task manquante")
            
            # Collecter
            if file_issues:
                issues.extend(file_issues)
            if file_warnings:
                warnings.extend([f"{prompt_file.name}: {w}" for w in file_warnings])
            
            print(f"    {prompt_file.name}: {len(content)} caractères")
            
        except Exception as e:
            print(f"  Erreur lecture {prompt_file.name}: {e}")
            issues.append(f"Erreur lecture {prompt_file.name}")
    
    # 2. Afficher les résultats
    if issues:
        print("\n PROBLÈMES CRITIQUES (sécurité):")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print("\nAVERTISSEMENTS (qualité):")
        for warning in warnings[:5]:  # Limiter l'affichage
            print(f"   • {warning}")
        if len(warnings) > 5:
            print(f"   ... et {len(warnings) - 5} avertissements supplémentaires")
    
    # 3. Vérifier la cohérence avec les logs
    print("\nVÉRIFICATION COHÉRENCE LOGS:")
    
    logs_file = Path(__file__).parent.parent.parent / "logs" / "experiment_data.json"
    if logs_file.exists():
        try:
            import json
            with open(logs_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Extraire les prompts utilisés dans les logs
            used_prompts = set()
            for log in logs:
                details = log.get('details', {})
                prompt = details.get('input_prompt', '')
                if prompt and len(prompt) > 20:
                    # Prendre les premiers 50 caractères comme signature
                    signature = prompt[:50].replace('\n', ' ').strip()
                    if signature:
                        used_prompts.add(signature)
            
            print(f"   Prompts uniques dans les logs: {len(used_prompts)}")
            
        except Exception:
            print("  Impossible d'analyser les logs")
    else:
        print(" Fichier de logs introuvable")
    
    print("\n" + "="*60)
    
    if not issues:
        print("PROMPTS VALIDÉS (sécurité OK)")
        return True
    else:
        print(" PROMPTS NON VALIDÉS - Données sensibles détectées")
        return False

def check_prompt_consistency():
    """Vérifie que les prompts sont cohérents entre les agents"""
    
    prompts_dir = Path(__file__).parent.parent.parent / "src" / "prompts"
    
    if not prompts_dir.exists():
        return True
    
    prompt_contents = {}
    
    # Lire tous les prompts
    for prompt_file in prompts_dir.glob("*.txt"):
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_contents[prompt_file.stem] = f.read().lower()
        except:
            pass
    
    if len(prompt_contents) < 2:
        return True 
    
    print("\nVÉRIFICATION COHÉRENCE ENTRE PROMPTS:")
    
    from difflib import SequenceMatcher
    
    prompts_list = list(prompt_contents.items())
    high_similarities = []
    
    for i in range(len(prompts_list)):
        for j in range(i + 1, len(prompts_list)):
            name1, content1 = prompts_list[i]
            name2, content2 = prompts_list[j]
            
            similarity = SequenceMatcher(None, content1, content2).ratio()
            
            if similarity > 0.8:  
                high_similarities.append((name1, name2, similarity))
    
    if high_similarities:
        print("Similarités élevées détectées:")
        for name1, name2, sim in high_similarities:
            print(f"   • {name1} ↔ {name2}: {sim:.1%}")
        print(" Les prompts devraient être différents par agent")
    else:
        print("Prompts suffisamment différents")
    
    return len(high_similarities) < 3 

if __name__ == "__main__":
    success1 = check_prompts_log()
    success2 = check_prompt_consistency()
    
    exit(0 if (success1 and success2) else 1)