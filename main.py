# main.py
import argparse
import os
import sys
from pathlib import Path
import json

from src.utils.logger import log_experiment, ActionType
from src.agents.auditor_agent_v1 import AuditorAgent
from src.agents.fixer_agent_v1 import FixerAgent
from src.agents.judje_agent_v1 import JudgeAgent  # Attention à l’orthographe



MAX_ITERATIONS = 1

def get_python_files(target_dir: str):
    """Récupère tous les fichiers Python dans le dossier et sous-dossiers."""
    python_files = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                python_files.append(os.path.join(root, f))
    return python_files

def main():
    parser = argparse.ArgumentParser(description="The Refactoring Swarm: Automatically refactor Python code")
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Path to the directory containing Python code"
    )
    args = parser.parse_args()
    target_dir = args.target_dir

    # Vérification du dossier
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        print(f"Erreur : {target_dir} n'est pas un dossier valide.")
        log_experiment(
            agent_name="System",
            model_used="N/A",
            action="ERROR",
            details={
                "input_prompt": "",
                "output_response": f"Invalid target: {target_dir}"
            },
            status="ERROR"
        )
        sys.exit(1)

    print(f"DEMARRAGE SUR : {target_dir}")
    log_experiment(
        agent_name="System",
        model_used="N/A",
        action="STARTUP",
        details={
            "input_prompt": "",
            "output_response": f"Target: {target_dir}"
        },
        status="INFO"
    )

    python_files = get_python_files(target_dir)
    if not python_files:
        print(f"Aucun fichier Python trouvé dans {target_dir}")
        log_experiment(
            agent_name="System",
            model_used="N/A",
            action="INFO",
            details={
                "input_prompt": "",
                "output_response": "No Python files found"
            },
            status="WARNING"
        )
        sys.exit(0)

    # -------------------------
    # Boucle de refactoring
    # -------------------------
    iteration = 0
    tests_passed = False

    auditor = AuditorAgent(verbose=True)
    fixer = FixerAgent(verbose=True)
    judge = JudgeAgent(verbose=True)

    while iteration < MAX_ITERATIONS and not tests_passed:
        print(f"\n--- Iteration {iteration + 1} ---")
        log_experiment(
            agent_name="System",
            model_used="N/A",
            action="ITERATION_START",
            details={
                "input_prompt": "",
                "output_response": f"Iteration {iteration + 1}"
            },
            status="INFO"
        )

        # -------------------------
        # Auditor phase
        # -------------------------
        refactoring_plans = {}
        for file_path in python_files:
            plan = auditor.analyze_file(Path(file_path))
            refactoring_plans[file_path] = plan
            log_experiment(
                agent_name="Auditor",
                model_used="gemini",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": "",
                    "output_response": json.dumps(plan)
                },
                status="SUCCESS"
            )

        # -------------------------
        # Fixer phase
        # -------------------------
        for file_path, plan in refactoring_plans.items():
            fixed_code, fixes = fixer.fix_file(Path(file_path), plan.get("refactoring_plan", []))
            if fixed_code:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
            log_experiment(
                agent_name="Fixer",
                model_used="gemini",
                action=ActionType.FIX,
                details={
                    "input_prompt": "",
                    "output_response": f"File fixed: {file_path}"
                },
                status="SUCCESS"
            )

        # -------------------------
        # Judge phase
        # -------------------------
        tests_passed = True
        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            result = judge.quick_evaluate(code)
            if not result:
                tests_passed = False
            log_experiment(
                agent_name="Judge",
                model_used="gemini",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": "",
                    "output_response": f"{file_path}: {'PASS' if result else 'FAIL'}"
                },
                status="SUCCESS" if result else "FAILURE"
            )

        iteration += 1

    # -------------------------
    # Rapport final
    # -------------------------
    if tests_passed:
        print("\nRefactoring terminé avec succès ✅")
        log_experiment(
            agent_name="System",
            model_used="N/A",
            action="MISSION_COMPLETE",
            details={
                "input_prompt": "",
                "output_response": f"Iterations: {iteration}"
            },
            status="INFO"
        )
    else:
        print("\nNombre maximal d'itérations atteint — arrêt sécurisé ⚠️")
        log_experiment(
            agent_name="System",
            model_used="N/A",
            action="MISSION_INCOMPLETE",
            details={
                "input_prompt": "",
                "output_response": f"Iterations: {iteration}"
            },
            status="WARNING"
        )

if __name__ == "__main__":
    main()
