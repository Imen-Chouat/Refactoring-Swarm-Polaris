from pathlib import Path
from langchain_groq import ChatGroq
from src.tools.file_tools import read_file
from src.utils.logger import log_experiment, ActionType  # ✅ Ajout
import os


groq_api_key = os.environ.get("GROQ_API_KEY")


class FixerAgent:
    def __init__(self, verbose: bool = False, groq_api_key: str = None):
        self.verbose = verbose

        # Initialisation du LLM Groq
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=groq_api_key,
        )

        # Lecture du prompt
        with open("src/prompts/fixer_prompt.txt", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def fix_file(self, file_path: Path, refactoring_plan: list):
        """Corrige le code en utilisant le plan de refactoring fourni."""
        if not refactoring_plan:
            if self.verbose:
                print(f"✅ Aucun problème à corriger pour {file_path}")
            return None, []

        # Lecture du code original
        code = read_file(str(file_path))

        # Création du prompt à envoyer à Groq
        prompt = f"""
{self.prompt_template}

ORIGINAL FILE:
{code}

REFACTORING PLAN:
{refactoring_plan}
"""

        if self.verbose:
            print(f"🚀 Envoi du fichier {file_path} à Groq pour correction...")

        # Appel à Groq
        response = self.llm.invoke(prompt)
        fixed_code = response.content

        if self.verbose:
            print(f"✅ Correction terminée pour {file_path}")

        # ✅ AJOUT : Logging de l'expérimentation
        log_experiment(
            agent_name="FixerAgent",
            model_used="llama-3.3-70b-versatile",
            action=ActionType.FIX,
            details={
                "file_fixed": str(file_path),
                "issues_count": len(refactoring_plan),
                "input_prompt": prompt,
                "output_response": fixed_code,
                "code_length_before": len(code),
                "code_length_after": len(fixed_code)
            },
            status="SUCCESS"
        )

        return fixed_code, refactoring_plan