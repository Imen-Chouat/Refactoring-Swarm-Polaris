# main.py
import argparse
import os
import sys
from dotenv import load_dotenv
from src.utils.logger import log_experiment
from src.agents.auditor_agent import run_auditor
from src.agents.fixer_agent import run_fixer
from src.agents.judge_agent import run_judge

# Load environment variables early
load_dotenv()

MAX_ITERATIONS = 10

def get_python_files(target_dir):
    """Recursively find all Python files in the target directory."""
    python_files = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                python_files.append(os.path.join(root, f))
    return python_files

def main():
    # -------------------------
    # Command-line argument parsing
    # -------------------------
    parser = argparse.ArgumentParser(description="The Refactoring Swarm: Automatically refactor Python code")
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Path to the directory containing buggy Python code"
    )
    args = parser.parse_args()
    target_dir = args.target_dir

    # -------------------------
    # Validate target directory
    # -------------------------
    if not os.path.exists(target_dir):
        print(f"Dossier {target_dir} introuvable.")
        log_experiment("System", "ERROR", f"Target not found: {target_dir}", "ERROR")
        sys.exit(1)

    if not os.path.isdir(target_dir):
        print(f"{target_dir} n'est pas un dossier valide.")
        log_experiment("System", "ERROR", f"Invalid directory: {target_dir}", "ERROR")
        sys.exit(1)

    print(f"DEMARRAGE SUR : {target_dir}")
    log_experiment("System", "STARTUP", f"Target: {target_dir}", "INFO")

    # -------------------------
    # Collect Python files
    # -------------------------
    python_files = get_python_files(target_dir)
    if not python_files:
        print(f"Aucun fichier Python trouvé dans {target_dir}")
        log_experiment("System", "INFO", "No Python files found", "WARNING")
        sys.exit(0)

    # -------------------------
    # Refactoring swarm loop
    # -------------------------
    iteration = 0
    tests_passed = False

    while iteration < MAX_ITERATIONS and not tests_passed:
        print(f"\n Iteration {iteration + 1}")
        log_experiment("System", "ITERATION_START", f"Iteration {iteration + 1}", "INFO")

        #AUDITOR PHASE
        refactoring_plans = {}
        for file_path in python_files:
            plan = run_auditor(file_path)
            refactoring_plans[file_path] = plan
            log_experiment("Auditor", "PLAN_CREATED", f"{file_path}: {plan}", "INFO")

        # FIXER PHASE
        for file_path, plan in refactoring_plans.items():
            run_fixer(file_path, plan)
            log_experiment("Fixer", "FILE_FIXED", f"{file_path}", "INFO")

        #  JUDGE PHASE
        tests_passed = run_judge(target_dir)
        log_experiment("Judge", "TESTS_PASSED", f"{tests_passed}", "INFO")

        iteration += 1

    # -------------------------
    # Completion report
    # -------------------------
    if tests_passed:
        print("\nRefactoring completed successfully")
        log_experiment("System", "MISSION_COMPLETE", f"Iterations: {iteration}", "INFO")
    else:
        print("\n Max iterations reached — stopping safely")
        log_experiment("System", "MISSION_INCOMPLETE", f"Iterations: {iteration}", "WARNING")


if __name__ == "__main__":
    main()
