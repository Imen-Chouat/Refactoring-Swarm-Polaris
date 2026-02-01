import json
import re
from pathlib import Path
from langchain_groq import ChatGroq
from src.tools.file_tools import read_file
from src.tools.pylint_tool import run_pylint
from src.utils.logger import log_experiment, ActionType  
import os

groq_api_key = os.environ.get("GROQ_API_KEY")

class AuditorAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=groq_api_key,
        )

        with open("src/prompts/auditor_prompt.txt", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def analyze_file(self, file_path: Path) -> dict:
        code = read_file(str(file_path))
        pylint_result = run_pylint(file_path)
        print("voici le resultat de pylint" ,pylint_result)
        pylint_output = pylint_result['output']

        prompt = f"""
{self.prompt_template}

PYTHON FILE:
{code}

PYLINT OUTPUT:
{pylint_output}
"""
        #if self.verbose:
            # print("=== PROMPT ENVOYÉ À GROQ ===")
            #print(prompt)
            #print("===============================")

        response = self.llm.invoke(prompt)

        if self.verbose:
            print("=== GROQ RESPONSE ===")
            print(response.content)
            print("=====================")

        try:
          issues = json.loads(response.content)
        except json.JSONDecodeError:
          issues = {
        "issues_found": 0,
        "refactoring_plan": [],
        "pylint_score": None,
        "summary": "Invalid JSON returned by model"
    }



        # Logging de l'analyse dans le système de suivi des expériences 
        log_experiment(
            agent_name="AuditorAgent",
            model_used="llama-3.3-70b-versatile",
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": str(file_path),
                "input_prompt": prompt,
                "output_response": response.content,
                "issues_detected": len(issues.get("refactoring_plan", []))
            },
            status="SUCCESS"
        )

        return {
            "refactoring_plan": issues.get("refactoring_plan", [])
        }