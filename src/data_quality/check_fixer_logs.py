import json 
import os 
from pathlib import Path
def check_fixer_logs():
    current_file = Path(__file__)  # C:\...\src\data_quality\check_auditor_logs.py
    project_root = current_file.parent.parent.parent  # C:\...\Refactoring-Swarm-Polaris
    logFile = project_root / "logs" / "experiment_data.json"  
    if not os.path.exists(logFile):
      print("/n LOG FILE NOT FOUND /n")
      return False
    with open(logFile,'r') as f:
        logs=json.load(f)
    fixerLogs=[log for log in logs if log.get('agent')=='Fixer']

    print(f"Fixer Agent Logs : {len(fixerLogs)} entries ")
    if not fixerLogs:
        print("No logs found for fixer agent ")
        print("/n the fixer agent did not call log_experiment_data function /n")
        return False

    stats={
        'total':len(fixerLogs),
        'success':0,
        'failure':0,
        'error':0,
        'with_input':0,
        'with_output':0,
        'files_fixed':set()
    }
    for log in fixerLogs:
        status=log.get('status','')
        if status=='SUCCESS':
            stats['success']+=1
        elif status=='FAILURE':
            stats['failure']+=1
        elif status=='ERROR':
            stats['error']+=1
    
        details=log.get('details',{})
        if details.get('input_prompt'):
            stats['with_input']+=1  
        if details.get('output_response'):
            stats['with_output']+=1  
        file_field=details.get('file_path') or details.get('file_fixed')
        if file_field:
            stats['files_fixed'].add(file_field)
    if stats['with_input'] < stats['total']:
             print(f"\n⚠️  {stats['total'] - stats['with_input']} logs sans input_prompt")
    if stats['with_output'] < stats['total']:
             print(f"⚠️  {stats['total'] - stats['with_output']} logs sans output_response")
    print(f"\n INFORMATIONS:")
    if stats['total'] == 0:
        print("THE FIXER DID NOT LOG ANY EXPERIMENT DATA")
    elif stats['success'] == 0:
        print("THE FILE DID NOT SUCCEED ")
    elif len(stats['files_fixed']) == 0:
        print("THE FIXER DID NOT SUCCEED IN FIXING ANY FILES")
    log_last=fixerLogs[-1]
    print(f"last log entry :")
    print(f"-Action : {log_last.get('action')}")
    print(f"-Status : {log_last.get('status')}")
    details=log_last.get('details',{})
    if 'input_prompt'not in details : 
        print("input_prompt missing in details ")
        return False
    if 'output_response' not in details : 
        print("output_response missing in details ")
        return False 
    print("Logs for fixer verified ")
    return True 



if __name__=="__main__":
    check_fixer_logs()