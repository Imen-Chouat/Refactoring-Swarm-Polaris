"""
Agent Judge - Évalue la qualité du code corrigé avec pytest et Pylint
"""

import os
import tempfile
from pathlib import Path

from langchain_groq import ChatGroq
from src.tools.pytest_tool import run_pytest
from src.tools.pylint_tool import run_pylint  #Utilisation directe
from src.utils.logger import log_experiment, ActionType


groq_api_key = os.environ.get("GROQ_API_KEY")


class JudgeAgent:
    """
    Agent qui évalue si le code corrigé respecte les standards.
    Utilise pytest pour les tests + Pylint pour la qualité.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=groq_api_key, 
        )
        self.model_name = "llama-3.3-70b-versatile"
        
        # Charger le prompt
        prompt_path = Path("src/prompts/judge_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt_text = f.read()
        else:
            self.prompt_text = "Tu es un juge de qualité de code Python."
        
        if self.verbose:
            print("JudgeAgent initialisé")
    
    def quick_evaluate(self, code: str, file_path: Path = None) -> dict:
        """
        Évalue rapidement la qualité du code avec pytest + Pylint.
        """
        result = {
            "passed": False,
            "pylint_score": None,
            "pytest_output": "",
            "errors": []
        }
        
        # Créer un fichier temporaire pour exécuter pytest dessus
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name
        
        try:
            # Exécuter pytest
            test_result = run_pytest(tmp_file_path)
            result["passed"] = test_result["passed"]
            result["pytest_output"] = test_result.get("output", "")
            
            # ✅ Exécuter pylint
            pylint_result = run_pylint(tmp_file_path)
            result["pylint_score"] = pylint_result.get("score")

            if self.verbose:
                status = "PASS" if result["passed"] else "FAIL"
                score = result["pylint_score"]
                score_str = f"{score:.2f}/10" if score is not None else "N/A"
                print(f"   [Judge] {tmp_file_path}: {status}, Pylint {score_str}")
            
            # Déterminer si le code est acceptable
            if not result["passed"]:
                result["errors"].append("Tests pytest ont échoué")
            
            if result["pylint_score"] is not None and result["pylint_score"] < 7.0:
                result["errors"].append(
                    f"Score Pylint insuffisant: {result['pylint_score']:.2f}/10 (minimum: 7.0)"
                )
                result["passed"] = False
            
            # Logger l'évaluation
            status = "SUCCESS" if result["passed"] else "FAILURE"
            self._log_evaluation(file_path or tmp_file_path, code, result, status)
            
            return result
            
        except FileNotFoundError as e:
            error_msg = f"pytest non installé: {e}"
            result["errors"].append(error_msg)
            if self.verbose:
                print(f"   ❌ {error_msg}")
                print("   💡 Installation: pip install pytest")
            self._log_evaluation(file_path, code, result, "FAILURE")
            return result
            
        except Exception as e:
            error_msg = f"Erreur lors de l'évaluation: {e}"
            result["errors"].append(error_msg)
            if self.verbose:
                print(f" {error_msg}")
            self._log_evaluation(file_path, code, result, "FAILURE")
            return result
            
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.remove(tmp_file_path)
            except Exception:
                pass
    
    def evaluate_file(self, file_path: Path) -> dict:
        """
        Évalue directement un fichier existant.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.quick_evaluate(code, file_path)
        except Exception as e:
            if self.verbose:
                print(f"Erreur lors de la lecture du fichier: {e}")
            return {
                "passed": False,
                "pylint_score": None,
                "pytest_output": "",
                "errors": [str(e)]
            }
    
    def _log_evaluation(self, file_path, code: str, result: dict, status: str):
        """Enregistre l'évaluation dans les logs"""
        log_experiment(
            agent_name="JudgeAgent",
            model_used=self.model_name,
            action=ActionType.DEBUG,
            details={
                "file_evaluated": str(file_path) if file_path else "in_memory",
                "input_prompt": f"Evaluating code ({len(code)} chars)",
                "output_response": f"Passed: {result['passed']}, Score: {result['pylint_score']}",
                "pytest_passed": result.get("passed", False),
                "pylint_score": result.get("pylint_score"),
                "errors": result.get("errors", []),
                "pytest_output_preview": result.get("pytest_output", "")[:200]
            },
            status=status
        )