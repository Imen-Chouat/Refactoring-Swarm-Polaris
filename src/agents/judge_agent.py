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
        Génère automatiquement des tests de base si aucun n'existe.
        """
        result = {
            "passed": False,
            "pylint_score": None,
            "pytest_output": "",
            "tests_generated": False,
            "errors": []
        }
        
        # 1. Créer le fichier de code temporaire
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(code)
            tmp_code_path = tmp_file.name
        
        # 2. Générer des tests automatiquement
        test_code = self._generate_basic_tests(code, tmp_code_path)
        
        # 3. Créer le fichier de test temporaire
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='_test.py',
            delete=False,
            encoding='utf-8'
        ) as tmp_test_file:
            tmp_test_file.write(test_code)
            tmp_test_path = tmp_test_file.name
        
        try:
            # 4. Exécuter pytest sur le fichier de test
            test_result = run_pytest(tmp_test_path)
            result["passed"] = test_result["passed"]
            result["pytest_output"] = test_result.get("output", "")
            result["tests_generated"] = True
            
            # 5. Exécuter pylint sur le code original
            pylint_result = run_pylint(tmp_code_path)
            result["pylint_score"] = pylint_result.get("score")
            
            if self.verbose:
                status = "PASS" if result["passed"] else "FAIL"
                score = result["pylint_score"]
                score_str = f"{score:.2f}/10" if score is not None else "N/A"
                print(f"   [Judge] Generated tests: {status}, Pylint {score_str}")
            
            # 6. Vérifier les critères d'acceptation
            if not result["passed"]:
                result["errors"].append("Generated tests failed")
            
            if result["pylint_score"] is not None and result["pylint_score"] < 7.0:
                result["errors"].append(
                    f"Score Pylint insuffisant: {result['pylint_score']:.2f}/10"
                )
                result["passed"] = False
            
            self._log_evaluation(file_path or tmp_code_path, code, result, 
                               "SUCCESS" if result["passed"] else "FAILURE")
            
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
            # Nettoyage des fichiers temporaires
            for path in [tmp_code_path, tmp_test_path]:
                try:
                    os.remove(path)
                except Exception:
                    pass
    
    def _generate_basic_tests(self, code: str, code_path: str) -> str:
        """
        Génère des tests basiques pour le code.
        Utilise le LLM Groq pour créer des tests pertinents.
        """
        # Extraire le nom du module du chemin
        module_name = Path(code_path).stem
        
        prompt = f"""
ROLE: Intelligent Python Test Generator with SEMANTIC UNDERSTANDING
TASK: Generate semantic pytest tests that validate BUSINESS LOGIC.

CRITICAL INSTRUCTIONS:
1. Understand what each function SHOULD DO based on its name and context
2. Generate tests with EXPECTED CORRECT VALUES, not just testing if code runs
3. Tests should FAIL if current implementation is wrong - this helps FixerAgent!
4. Return ONLY the test code, no explanations

SEMANTIC ANALYSIS:
- "calculate_average([10, 20])" should return 15.0 (sum/len), NOT 30.0 (sum)
- "validate_email("test@example.com")" should return True for valid emails
- "add(2, 3)" should return 5
- "divide(10, 2)" should return 5.0
- "sort_list([3,1,2])" should return [1,2,3]

TEST GENERATION RULES:
1. For EACH function, determine its SEMANTIC PURPOSE from its name
2. Generate tests with ASSERTIONS containing EXPECTED VALUES
3. Include normal cases, edge cases, and error cases
4. Each test must have a descriptive docstring
5. Import using: import {module_name}

EXAMPLES OF SEMANTIC ASSERTIONS:
assert {module_name}.calculate_average([10, 20]) == 15.0  # NOT 30.0!
assert {module_name}.add(2, 3) == 5
assert {module_name}.divide(10, 2) == 5.0

PYTHON CODE TO TEST:
{code}

MODULE NAME: {module_name}
FILE PATH: {code_path}

IMPORT INSTRUCTIONS:
- Since test runs in same directory, use: import {module_name}
- Or use relative import if appropriate
- If code has main block (if __name__ == "__main__"), test the functions directly

IMPORTANT: If function "calculate_average" returns sum instead of average,
the test SHOULD FAIL with assertion error: "Expected 15.0, got 30.0"

GENERATED SEMANTIC TEST CODE (Python only, no markdown):
"""
        
        try:
            response = self.llm.invoke(prompt)
            test_code = response.content
            
            # Nettoyer la réponse si nécessaire
            if "```python" in test_code:
                test_code = test_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_code:
                test_code = test_code.split("```")[1].strip()
            
            # Vérifier que le code contient au moins une fonction test_
            if "def test_" not in test_code:
                raise ValueError("Generated code doesn't contain test functions")
            
            return test_code
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  LLM test generation failed: {e}, using fallback")

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
                "tests_generated": False,
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
                "tests_generated": result.get("tests_generated", False),
                "errors": result.get("errors", []),
                "pytest_output_preview": result.get("pytest_output", "")[:500]
            },
            status=status
        )
