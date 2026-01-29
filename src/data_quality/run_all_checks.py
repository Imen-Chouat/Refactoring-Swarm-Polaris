#!/usr/bin/env python3
# Exécution de toutes les vérifications 
import sys
import importlib.util
from pathlib import Path


def run_all_checks():
    print("=" * 70)
    print("📊 AUDIT COMPLET - DATA OFFICER")
    print("=" * 70)
    
    # Ajouter le dossier courant au path pour les imports
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(current_dir.parent))
    
    results = {}
    
    # 1. Vérification des logs principaux
    print("\n1. VÉRIFICATION LOGS GÉNÉRAUX")
    print("-" * 40)
    try:
        # Essayer d'importer validate_log
        validate_path = project_root / "src" / "utils" / "validate_log.py"
        if validate_path.exists():
            spec = importlib.util.spec_from_file_location("validate_log", str(validate_path))
            validate_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validate_module)
            results["general_logs"] = validate_module.validate_log()
        else:
            print("  ⚠️  validate_log.py non trouvé.")
            from data_quality.check_all_agents import check_all_agents
            results["general_logs"] = check_all_agents()
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        results["general_logs"] = False
    
    # 2. Vérification par agent
    print("\n2. VÉRIFICATION PAR AGENT")
    print("-" * 40)
    
    checks = [
        ("Auditor", "check_auditor_logs"),
        ("Fixer", "check_fixer_logs"),
        ("Judge", "check_judge_logs")
    ]
    
    for agent_name, module_name in checks:
        try:
            module_path = current_dir / f"{module_name}.py"
            if module_path.exists():
                print(f"  📂 Chargement {module_name}...")
                spec = importlib.util.spec_from_file_location(module_name, str(module_path))
                module_obj = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module_obj)
                check_func = getattr(module_obj, module_name)
                results[f"agent_{agent_name.lower()}"] = check_func()
                print(f"  ✓ {agent_name}: Test terminé")
            else:
                print(f"  ⚠️  {agent_name}: Fichier {module_name}.py non trouvé")
                results[f"agent_{agent_name.lower()}"] = False
        except Exception as e:
            print(f"  ❌ {agent_name}: Erreur - {str(e)[:100]}")
            results[f"agent_{agent_name.lower()}"] = False
    
    # 3. Vérification outils
    print("\n3. VÉRIFICATION OUTILS")
    print("-" * 40)
    try:
        tools_path = current_dir / "check_tools_log.py"
        if tools_path.exists():
            spec = importlib.util.spec_from_file_location("check_tools_log", str(tools_path))
            tools_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tools_module)
            results["tools_logging"] = tools_module.check_tools_log()
            results["tools_security"] = tools_module.check_tool_imports()
            print("  ✓ Vérification outils terminée")
        else:
            print("  ⚠️  check_tools_log.py non trouvé")
            results["tools_logging"] = False
            results["tools_security"] = False
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        results["tools_logging"] = False
        results["tools_security"] = False
    
    # 4. Vérification prompts
    print("\n4. VÉRIFICATION PROMPTS")
    print("-" * 40)
    try:
        prompts_path = current_dir / "check_prompts_log.py"
        if prompts_path.exists():
            spec = importlib.util.spec_from_file_location("check_prompts_log", str(prompts_path))
            prompts_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(prompts_module)
            results["prompts_security"] = prompts_module.check_prompts_log()
            results["prompts_consistency"] = prompts_module.check_prompt_consistency()
            print("  ✓ Vérification prompts terminée")
        else:
            print("  ⚠️  check_prompts_log.py non trouvé")
            results["prompts_security"] = False
            results["prompts_consistency"] = False
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        results["prompts_security"] = False
        results["prompts_consistency"] = False
    
    # 5. Vérification complète système
    print("\n5. VÉRIFICATION COMPLÈTE SYSTÈME")
    print("-" * 40)
    try:
        all_agents_path = current_dir / "check_all_agents.py"
        if all_agents_path.exists():
            spec = importlib.util.spec_from_file_location("check_all_agents", str(all_agents_path))
            all_agents_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(all_agents_module)
            results["complete_system"] = all_agents_module.check_all_agents_logs()
            print("  ✓ Vérification système terminée")
        else:
            print("  ⚠️  check_all_agents.py non trouvé")
            results["complete_system"] = False
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        results["complete_system"] = False
    
    # 6. Résumé final
    print("\n" + "=" * 70)
    print("📈 RÉSUMÉ FINAL - DATA OFFICER")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    score = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n✅ Tests passés: {passed}/{total} ({score:.1f}%)")
    
    print("\n📋 DÉTAIL DES RÉSULTATS:")
    for check_name, success in sorted(results.items()):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status:10} : {check_name}")
    
    print("\n" + "=" * 70)
    
    # Recommandations
    if score >= 90:
        print("🎉 EXCELLENT - Système prêt pour soumission!")
        print("  Votre travail de Data Officer est terminé.")
        final_success = True
    elif score >= 70:
        print("👍 SATISFAISANT - Quelques améliorations possibles")
        print("  Vérifiez les tests échoués ci-dessus.")
        final_success = True
    elif score >= 50:
        print("⚠️  MOYEN - Corrections nécessaires")
        print("  Le système risque d'échouer aux critères de qualité.")
        final_success = False
    else:
        print("❌ INSUFFISANT - Travail important nécessaire")
        print("  La note 'Qualité des Données' sera faible.")
        final_success = False
    
    print("\n💡 PROCHAINES ÉTAPES:")
    if not results.get("general_logs", False):
        print("  • Exécuter: python src/utils/validate_logs.py")
    if not results.get("complete_system", False):
        print("  • Exécuter: python src/data_quality/check_all_agents.py")
    if not results.get("prompts_security", False):
        print("  • Vérifier les clés API dans les prompts")
    
    # Affichage des problèmes spécifiques
    print("\n🔍 PROBLÈMES SPÉCIFIQUES À CORRIGER:")
    if not results.get("agent_auditor", True):
        print("  • L'Auditor Agent ne loggue pas correctement")
    if not results.get("agent_fixer", True):
        print("  • Le Fixer Agent ne loggue pas correctement")
    if not results.get("agent_judge", True):
        print("  • Le Judge Agent ne loggue pas correctement")
    if not results.get("tools_logging", True):
        print("  • Les outils ne loggent pas correctement")
    if not results.get("prompts_security", True):
        print("  • Des données sensibles détectées dans les prompts")
    
    return final_success


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)