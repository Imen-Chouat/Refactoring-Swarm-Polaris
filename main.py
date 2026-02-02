import os
import sys
from pathlib import Path

from src.agents.auditor_agent import AuditorAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.judge_agent import JudgeAgent
from dotenv import load_dotenv


def get_python_files(target_dir: str):
    """Récupère tous les fichiers Python dans le dossier et sous-dossiers."""
    python_files_list = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                python_files_list.append(os.path.join(root, f))
    return python_files_list


def main():
    target_dir = "./sandbox"
    if not os.path.exists(target_dir):
        print(f"Dossier {target_dir} introuvable . Veuillez créer un dossier 'sandbox' avec des fichiers Python à analyser.")
        sys.exit(1)

    # Charger les variables d'environnement
    load_dotenv()
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("La variable d'environnement GROQ_API_KEY n'est pas définie . Veuillez la définir dans le fichier .env.")

    # Initialisation des agents
    auditor = AuditorAgent(verbose=True)
    fixer = FixerAgent(verbose=True)
    judge = JudgeAgent(verbose=True)

    python_files_list = get_python_files(target_dir)
    if not python_files_list:
        print("Aucun fichier Python trouvé (dans le dossier 'sandbox'.")
        return

    for py_file in python_files_list:
        print(f"\n{'='*60}")
        print(f"1 ere etape - Analyse de {py_file} : ")
        print(f"{'='*60}")

        # 1 st step AUDIT
        result = auditor.analyze_file(Path(py_file))
        refactoring_plan = result.get("refactoring_plan", [])

        if not refactoring_plan:
            print("Aucun problème détecté — passage au fichier suivant.")
            continue

        print(f"{len(refactoring_plan)} problème(s) détecté(s): ")
        for i, Singleissue in enumerate(refactoring_plan, 1):
            print(f"  {i}. [{Singleissue.get('priority','UNKNOWN')}] {Singleissue.get('issue','No description')}")
            print(f"     [{Singleissue.get('category','UNKNOWN')}] {Singleissue.get('issue','No description')}")
            print(f"     Ligne {Singleissue.get('line','?')}: {Singleissue.get('code_snippet','')}")
            print(f"     Suggestion: {Singleissue.get('suggestion','')}")

        # 2 nd step : FIX
        fixed_code, _ = fixer.fix_file(Path(py_file), refactoring_plan)
        if fixed_code:
            with open(py_file, "w", encoding="utf-8") as f:
                f.write(fixed_code)

        # 3rd step JUDGE - Tests unitaires
        print(f"\n Génération et exécution des tests unitaires...")
        with open(py_file, 'r', encoding='utf-8') as f:
            code_content = f.read()
        judge_result = judge.quick_evaluate(code_content, py_file)

        # 4th step SELF-HEALING LOOP - Correction basée sur les tests
        max_iterations = 30
        iteration = 0
        print(f"\n Démarrage de la boucle de self-healing (max {max_iterations} itérations)...")
                
        while iteration < max_iterations and not judge_result["passed"]:
         iteration += 1
         print(f"\n{'─'*60}")
         print(f"Itération {iteration}/{max_iterations}")
         print(f"{'─'*60}")

         refactoring_test = judge_result.get("refactoring_test_failure")
         if not refactoring_test:
          print("Aucun problème détecté par les tests — sortie de la boucle de self-healing.")
          break  # Sortir si rien à corriger 
       
         print(f"\n {refactoring_test.get('issues_found', 0)} problème(s) détecté(s) par les tests: ")
         for i, Singleissue in enumerate(refactoring_test.get("refactoring_plan", []), 1):
          print(f"  {i}. [{Singleissue.get('priority','UNKNOWN')}] {Singleissue.get('issue','No description')}")
          print(f"     Catégorie: [{Singleissue.get('category','UNKNOWN')}]")
          print(f"     Message: {Singleissue.get('error_message','')[:150]}")
          print(f"     Suggestion: {Singleissue.get('suggestion','')}")
          print(f"     Requiert main protection: {Singleissue.get('requires_main_protection', False)}")

            # Correction
         fixed_code, _ = fixer.fix_file(Path(py_file), refactoring_test)
         if fixed_code:
                with open(py_file, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                print(f"\nCode corrigé pour {py_file}:\n")
                print(fixed_code)

            # Réévaluation
         judge_result = judge.quick_evaluate(fixed_code, py_file)

         if judge_result.get("passed", False):
                print("Tests réussis — Mission terminée avec succès !")
                break
         else:
                print("Tests échoués — Retour au Fixer (Self-Healing Loop) ...")


if __name__ == "__main__":
    main()