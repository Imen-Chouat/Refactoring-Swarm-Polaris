from pathlib import Path
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.file_tools import read_file
from src.tools.pylint_tool import run_pylint


class AuditorAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash",
            temperature=0
        )

 # Load the text prompt template for the auditor from a file
        with open("src/prompts/auditor_prompt_v2.txt", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def analyze_file(self, file_path: Path) -> dict:
           # Read the full content of the Python file
        code = read_file(str(file_path))
           # Run pylint to get static code analysis results
        pylint_output = run_pylint(file_path)

        prompt = f"""
{self.prompt_template}

PYTHON FILE:
{code}

PYLINT OUTPUT:
{pylint_output}
"""

        response = self.llm.invoke(prompt)
        # Attempt to parse the AI response as JSON
        # If it fails, return an empty list of issues
        try:
            issues = json.loads(response.content)
        except json.JSONDecodeError:
            issues = {"issues": []}

        # je l'ai adapter au main de wissem
        return {
            "refactoring_plan": issues.get("issues", [])
        }