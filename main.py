import os
import sys
from pathlib import Path

from src.agents.auditor_agent import AuditorAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.judge_agent import JudgeAgent
from dotenv import load_dotenv


def get_python_files(target_dir: str):
    """Récupère tous les fichiers Python dans le dossier et sous-dossiers."""
    python_files = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                python_files.append(os.path.join(root, f))
    return python_files


def main():
    target_dir = "./sandbox"
    if not os.path.exists(target_dir):
        print(f" Dossier {target_dir} introuvable")
        sys.exit(1)

    # 🔹 Charger les variables d'environnement
    load_dotenv()
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError(" La variable d'environnement GROQ_API_KEY n'est pas définie")

    # 🔹 Initialisation des agents
    auditor = AuditorAgent(verbose=True)
    fixer = FixerAgent(verbose=True)
    judge = JudgeAgent(verbose=True)

    python_files = get_python_files(target_dir)
    if not python_files:
        print(" Aucun fichier Python trouvé")
        return

    for py_file in python_files:
        print(f"\n{'='*40}")
        print(f"Analyse de {py_file}")
        print(f"{'='*40}")

        # AUDIT
        result = auditor.analyze_file(Path(py_file))
        refactoring_plan = result.get("refactoring_plan", [])

        if not refactoring_plan:
            print(" Aucun problème détecté")
            continue

        print(f" {len(refactoring_plan)} problème(s) détecté(s):")
        for i, issue in enumerate(refactoring_plan, 1):
            print(
                f"  {i}. [{issue.get('category','UNKNOWN')}] "
                f"{issue.get('issue','No description')}"
            )

        #FIX
        fixed_code, _ = fixer.fix_file(Path(py_file), refactoring_plan)

        if fixed_code:
            with open(py_file, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            # 3️⃣ JUDGE (tests)
            tests_passed = judge.quick_evaluate(fixed_code)

            if tests_passed["passed"]:
                print("Tests réussis — Mission terminée 🎉")
            else:
                print("Tests échoués — Retour au Fixer (Self-Healing Loop)")


if __name__ == "__main__":
    main()