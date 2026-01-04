from src.utils.logger import log_experiment, ActionType
import json
import os

LogFile_path=os.path.join("logs","experiment_data.json")

def ValidateLogEntry(entry):
    fields_check=["id","timestamp","agent","model","action","details","status"]
    details_check=["input_prompt","output_response"]
    
    missing_fields=[field for field in fields_check if field not in entry ]
    missing_details=[detail for detail in details_check if detail not in entry["details"]]

    if missing_fields :
        return False,f"Essentails fields in the  are missing : { missing_fields}"

    if missing_details: 
        return False, f"Essentails fields in the details are missing : { missing_details}"
    return True,"All required fields are present ."
Agents=[
        ("Auditor ",ActionType.ANALYSIS,{"input_prompt":"Test log for auditor ","output_response":{"issues":[{"type":"logic ","description":"Bug","line":42}]}}, "SUCCESS"),
        ("Fixer ",ActionType.FIX,{"input_prompt":"Test log for fixer ","output_response":{"issues":[{"type":"syntax ","description":"Bug","line":14}]}}, "SUCCESS"),
        ("Generator ",ActionType.GENERATION,{"input_prompt":"Test log for judge ","output_response":{"issues":[{"type":"style ","description":"Bug","line":4}]}}, "SUCCESS"),
]
for agent_name,action_type,details,status in Agents : 
        log_experiment(
            agent_name =agent_name,
            model_used="gemini-test-model",
            action=action_type,
            details=details,
            status=status
        )
        print(f"Logger work for {agent_name }")
   
if os.path.exists(LogFile_path):
        with open(LogFile_path,"r",encoding="utf-8") as f:
            dataset=json.load(f)
            print(f"\n the JSON file contain ({len(dataset)} logs ):")
            for i, entry in enumerate(dataset[-len(Agents):],1):
                state,message=ValidateLogEntry(entry)
                print(f"\nlog #{i} - Agent : {entry['agent']}")
                print(f"validation: {message}")
                print(json.dumps(entry,indent=4,ensure_ascii=False))
else:
        print(f"\n Log file not Found ")
auditor_output = {"issues": [{"type": "logic", "description": "Bug simulé", "line": 10}]}
log_experiment("Auditor", "gemini-test-model", ActionType.ANALYSIS,
               {"input_prompt": "Vérifier le code", "output_response": auditor_output}, "SUCCESS")

# Fixer applique la correction
fixer_output = "def add(a, b):\n    return a + b"
log_experiment("Fixer", "gemini-test-model", ActionType.FIX,
               {"input_prompt": "Appliquer corrections", "output_response": fixer_output}, "SUCCESS")

# Judge valide les tests
judge_output = "Tous les tests passés"
log_experiment("Judge", "gemini-test-model", ActionType.DEBUG,
               {"input_prompt": "Exécuter tests", "output_response": judge_output}, "SUCCESS")

print("✅ Mini-cycle complet simulé et loggé avec succès")                    