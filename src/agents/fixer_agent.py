from pathlib import Path
from langchain_groq import ChatGroq
from src.tools.file_tools import read_file
from src.utils.logger import log_experiment, ActionType 
import os


groq_api_key = os.environ.get("GROQ_API_KEY")


class FixerAgent:
    def __init__(self, verbose: bool = False, groq_api_key: str = None):
        self.verbose = verbose

        # Initialisation du LLM Groq - Groq LLM initialization
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=groq_api_key,
        )

        # Lecture du prompt de correction de code - read the code fixing prompt
        with open("src/prompts/fixer_prompt.txt", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def fix_file(self, file_path: Path, refactoring_plan: list):
        """Corrige le code en utilisant le plan de refactoring fourni par l'AuditorAgent."""
        if not refactoring_plan:
            if self.verbose:
                print(f"Aucun problème à corriger pour {file_path}  — passage au fichier suivant.")
            return None, []

        # Lecture du code original du fichier à corriger - read the original code from the file to be fixed
        code = read_file(str(file_path))

        # Création du prompt à envoyer à Groq LLM pour correction du code - create the prompt to send to Groq LLM for code fixing
        prompt = f"""
{self.prompt_template}

ORIGINAL FILE:
{code}

REFACTORING PLAN:
{refactoring_plan}
"""

        if self.verbose:
            print(f"Envoi du fichier {file_path} à Groq pour correction...")

        # Appel à Groq LLM pour obtenir le code corrigé - Call Groq LLM to get the fixed code
        response = self.llm.invoke(prompt)
        fixed_code = response.content
        
        #Nettoyage du code généré - Cleaning the generated code
        fixed_code = self._clean_generated_code(fixed_code)

        if self.verbose:
            print(f"Correction terminée pour {file_path} .")

        # Logging the experiment in the experiment tracking system - Logging de l'expérimentation dans le système de suivi des expériences 
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
    
    def _clean_generated_code(self, code: str) -> str:
        """
        Nettoie le code généré par le LLM.
        Supprime les markdown, explications, et formatage indésirable. 
        """
        # Supprimer les balises markdown ```python et ```
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        # Supprimer les lignes qui commencent par des explications
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Ignorer les lignes vides répétées au début
            if not cleaned_lines and not line.strip():
                continue
            
            # Ignorer les explications type "Here's the fixed code:" - Ignore explanation lines
            if line.strip().lower().startswith(('here', 'the fixed', 'i have', 'i\'ve')):
                continue
            
            # Remove repeated FIXME comments - Supprimer les commentaires FIXME répétés (bug de génération) 
            if line.strip().startswith('# FIXME:'):
                # Ne garder que le premier FIXME par fichier
                if cleaned_lines and any('# FIXME:' in l for l in cleaned_lines):
                    continue
            
            cleaned_lines.append(line)
        
        # Rejoindre les lignes nettoyées - Join cleaned lines together
        cleaned_code = '\n'.join(cleaned_lines)
        
        # Supprimer les espaces en fin de ligne - Remove trailing spaces at the end of lines 
        cleaned_code = '\n'.join(line.rstrip() for line in cleaned_code.split('\n'))
        
        # S'assurer qu'il y a une ligne vide à la fin - Ensure there's a newline at the end of the file
        if cleaned_code and not cleaned_code.endswith('\n'):
            cleaned_code += '\n'
        
        return cleaned_code