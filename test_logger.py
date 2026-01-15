from src.utils.logger import log_experiment, ActionType

log_experiment(
    agent_name="Auditor",
    model_used="test-model",
    action=ActionType.ANALYSIS,
    details={
        "input_prompt": "Test du logger",
        "output_response": "Le logger fonctionne"
    },
    status="SUCCESS"
)

print("Logger fonctionne pour auditor ")
log_experiment(
    agent_name="Fixer",
    model_used="test-model",        
    action=ActionType.FIX,
    details={
        "input_prompt": "Test du logger pour fixer",
        "output_response": "Le logger fonctionne pour fixer"
    },          
    status="SUCCESS"

)
print("Logger fonctionne pour fixer ")
log_experiment(
    agent_name="Generator",
    model_used="test-model",        
    action=ActionType.GENERATION,
    details={
        "input_prompt": "Test du logger pour judger",
        "output_response": "Le logger fonctionne pour judger"
    },          
    status="SUCCESS"

)
print("Logger fonctionne pour judger ")