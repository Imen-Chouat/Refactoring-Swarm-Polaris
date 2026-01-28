import json 
import os 
from pathlib import Path 
def check_judge_logs():
    current_file = Path(__file__)  # C:\...\src\data_quality\check_auditor_logs.py
    project_root = current_file.parent.parent.parent  # C:\...\Refactoring-Swarm-Polaris
    logFile = project_root / "logs" / "experiment_data.json" 
    if not os.path.exists(logFile):
        print("/n LOG FILE NOT FOUND /n")
        return False
    with open(logFile,'r') as f:
        logs=json.load(f)
    judgeLogs=[log for log in logs if log.get('agent')=='Judge']
    print(f"Judge Agent Logs : {len(judgeLogs)} entries ")
    if not judgeLogs:
        print("No logs found for judge agent ")
        print("/n the judge agent did not call log_experiment_data function /n")
        return False
    
    log_last=judgeLogs[-1]
    print(f"last log entry :")
    print(f"-Action : {log_last.get('action')}")
    print(f"-Status : {log_last.get('status')}")
    details=log_last.get('details',{})
    if 'input_prompt'not in details : 
        print("input_prompt missing in details ")
        return False
    if 'output_prompt' not in details : 
        print("output_prompt missing in details ")
        return False 
    print("Logs for judge verified ")
    return True 
if __name__=="__main__":
    check_judge_logs()