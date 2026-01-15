import os
import json
from src.utils.logger import log_experiment, ActionType
from llm_client import call_llm  # ton LLM mock

# --- 1️⃣ Charger le prompt Auditor v2 ---
PROMPT_PATH = "src/prompts/auditor_prompt_v1.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    auditor_prompt = f.read()

# --- 2️⃣ Dossier des fichiers Python cassés ---
DATASET_DIR = "sandbox/dataset_test/"

# --- 3️⃣ Fonction de validation des logs ---
def validate_log_entry(entry):
    required_fields = ["id", "timestamp", "agent", "model", "action", "details", "status"]
    required_details = ["input_prompt", "output_response"]

    missing_fields = [f for f in required_fields if f not in entry]
    missing_details = [d for d in required_details if d not in entry.get("details", {})]

    if missing_fields:
        return False, f"Missing fields in log: {missing_fields}"
    if missing_details:
        return False, f"Missing fields in details: {missing_details}"
    return True, "All required fields are present."

# --- 4️⃣ Parcourir tous les fichiers cassés ---
for filename in os.listdir(DATASET_DIR):
    if filename.endswith(".py"):
        file_path = os.path.join(DATASET_DIR, filename)

        # Lire le contenu du fichier (optionnel, si tu veux passer au LLM)
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()

        # --- 5️⃣ Appeler le LLM mock pour Auditor ---
        prompt_for_file = auditor_prompt + f"\n\n# Code à analyser:\n{code_content}"
        response_str = call_llm(prompt_for_file, model_name="gemini-test-model")

        # Convertir en JSON
        try:
            auditor_output = json.loads(response_str)
        except json.JSONDecodeError:
            auditor_output = {"issues": [{"type": "logic", "description": "Mock JSON parse failed", "line": 0}]}

        # --- 6️⃣ Log le résultat ---
        log_experiment(
            agent_name="Auditor",
            model_used="gemini-test-model",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": prompt_for_file,
                "output_response": auditor_output
            },
            status="SUCCESS"
        )

        print(f"✅ Auditor logged for {filename}")

# --- 7️⃣ Vérifier les logs ---
LOG_FILE = "logs/experiment_data.json"
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)
        print(f"\nTotal logs: {len(logs)}")
        for entry in logs[-len(os.listdir(DATASET_DIR)):]:
            state, message = validate_log_entry(entry)
            print(f"Log #{entry['agent']} validation: {message}")

print("🎯 DAY 3 test complete: Auditor logs generated and validated!")
