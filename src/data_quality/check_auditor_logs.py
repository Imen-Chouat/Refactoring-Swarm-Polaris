import json 
import os
from pathlib import Path 

def check_auditor_logs():
    current_file = Path(__file__)  # C:\...\src\data_quality\check_auditor_logs.py
    project_root = current_file.parent.parent.parent  # C:\...\Refactoring-Swarm-Polaris
    LOG_FILE = project_root / "logs" / "experiment_data.json"
    if not os.path.exists(LOG_FILE):
        print("/n LOG FILE NOT FOUND /n")
        return False
    with open(LOG_FILE,'r') as f:
        logs=json.load(f)
    auditorLogs=[log for log in logs if log.get('agent')=='Auditor']
    print(f"auditor Agent Logs : {len(auditorLogs)} entries ")
    if not auditorLogs:
        print("No logs found for auditor agent ")
        print("/n the auditor agent did not call log_experiment_data function /n")
        return False

    log_last=auditorLogs[-1]
    print(f"last log entry :")
    print(f" -Action : {log_last.get('action')}")
    print(f"-Status : {log_last.get('status')}")
    details=log_last.get('details',{})
    if 'input_prompt'not in details : 
        print("input_prompt missing in details ")
        return False
    if 'output_prompt' not in details : 
        print("output_prompt missing in details ")
        return False 
    print("Logs for auditor verified ")
    return True 
if __name__=="__main__":
    check_auditor_logs()