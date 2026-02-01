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
        result_final = {
            "passed": False,
            "pylint_score": None,
            "pytest_output": "",
            "pylint_output": "",
            "tests_generated": False,
            "pytest_passed":False,
            "errors": [],
            "refactoring_test_failure": None
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

        # Affichage du fichier de test pour inspection - Display test file for inspection 
        print(f"\nFichier de test temporaire créé : {tmp_test_path}")
        print("Contenu du fichier de test :\n")
        print(test_code)
        
        try:
            # 4. Exécuter pytest sur le fichier de test
            test_result = run_pytest(tmp_test_path)
            result_final["pytest_passed"] = test_result["passed"]
            result_final["pytest_output"] = test_result.get("output", "")
            result_final["tests_generated"] = True
            
            # Affichage du résultat complet de pytest - Display full pytest result
            print("\n Résultat de pytest :")
            print(result_final["pytest_output"])

            # 6. Exécuter pylint sur le code original - Run pylint on the original code - Direct use of pylint tool 
            pylint_result_dictionary = run_pylint(tmp_code_path)
            result_final["pylint_score"] = pylint_result_dictionary.get("score")
            result_final["pylint_output"] = pylint_result_dictionary.get("output")
            print("resultat pylint",result_final["pylint_output"])


            if result_final["pytest_passed"] and result_final["pylint_score"] is not None and result_final["pylint_score"] >= 7.0:
             result_final["passed"] = True
            else:
             result_final["passed"] = False


            
            print("le resultat est ",result_final)
            # 5. Analyser les échecs de tests et problèmes de code avec LLM si nécessaire - Analyze test failures and code issues with LLM if needed
            needs_analysis = False
            pytest_output_to_analyze = None
            pylint_output_to_analyze = None

            # Vérifier si les tests unitaires ont échoué - Check if unit tests failed 
            if not result_final["pytest_passed"]:
               needs_analysis = True
               pytest_output_to_analyze = result_final["pytest_output"]

            # Vérifier si le score Pylint est insuffisant - Check if Pylint score is insufficient
            if result_final.get("pylint_score") is not None and result_final["pylint_score"] < 7.0:
              needs_analysis = True
              pylint_output_to_analyze = result_final.get("pylint_output")

            if needs_analysis:
                   if self.verbose:
                      print("\n Analyse combinée des échecs de tests et du code...")
                      
                   # Appeler fonction qui combine pytest + pylint outputs - Call function that combines pytest + pylint outputs
                   analysis = self._analyze_failures(
                    code,
                    pytest_output=pytest_output_to_analyze,
                    pylint_output=pylint_output_to_analyze,
                    pylint_score=result_final.get("pylint_score")
                   )
    
                   result_final["refactoring_test_failure"] = analysis
                   if self.verbose:
                      print(f" Refactoring disponible dans result_final['refactoring_test_failure']")
                      print(result_final["refactoring_test_failure"])



            
            if self.verbose:
                status = "YES" if result_final["tests_generated"] else "NO"
                score = result_final["pylint_score"]
                score_str = f"{score:.2f}/10" if score is not None else "N/A"
                print(f"   [Judge] Generated tests: {status}")
            
            # 7. Vérifier les critères d'acceptation finale - Check final acceptance criteria
            if not result_final["pytest_passed"]:
                result_final["errors"].append("Generated tests failed")
            
            # Déterminer le status final pour le log 
            if not result_final.get("pytest_passed", False) or result_final["pylint_score"] is None or result_final["pylint_score"] < 7.0:
              log_status = "FAILURE"
            else:
              log_status = "SUCCESS"

            self._log_evaluation(file_path or tmp_code_path, code, result_final, status=log_status)
            
            return result_final
            
        except FileNotFoundError as e:
            error_msg = f"pytest non installé: {e}"
            result_final["errors"].append(error_msg)
            if self.verbose:
                print(f"Error ,  {error_msg}")
                print(" Installation: pip install pytest")
            self._log_evaluation(file_path, code, result_final, "FAILURE")
            return result_final
            
        except Exception as e:
            error_msg = f"Erreur lors de l'évaluation: {e}"
            result_final["errors"].append(error_msg)
            if self.verbose:
                print(f" {error_msg}")
            self._log_evaluation(file_path, code, result_final, "FAILURE")
            return result_final
            
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
ROLE: Expert Python Test Generator with SEMANTIC UNDERSTANDING
TASK: Generate comprehensive pytest tests that detect bugs and validate functionality.

═══════════════════════════════════════════════════════════════════
UNIVERSAL TEST GENERATION STRATEGY
═══════════════════════════════════════════════════════════════════

CRITICAL INSTRUCTIONS:
1. Analyze each function to determine if it's SEMANTIC or CUSTOM
2. Generate tests with EXPECTED CORRECT VALUES based on function category
3. Tests should FAIL if current implementation is wrong - this helps FixerAgent!
4. Return ONLY the test code, no explanations, no markdown

STEP 1: CLASSIFY EACH FUNCTION

Category A - SEMANTIC FUNCTIONS (test against semantic meaning):
  • add, subtract, multiply, divide, diviser
  • calculate_average, get_average, compute_mean, mean
  • validate_email, check_email, is_valid_email
  • sort_list, sort_array, sorted_list
  • max, min, sum (when used as function names)

Category B - CUSTOM/AMBIGUOUS FUNCTIONS (test implementation + edge cases):
  • Business logic functions
  • Functions with unclear names
  • Domain-specific functions
  • Misspelled function names (e.g., "valdiate")

═══════════════════════════════════════════════════════════════════
SEMANTIC EXPECTATIONS (Category A - STRICT MODE)
═══════════════════════════════════════════════════════════════════

These functions MUST follow their semantic meaning:

add/addition:
  add(2, 3) == 5 (addition, NOT multiplication)
  add(0, 5) == 5
  add(-2, 3) == 1
  add(-2, -3) == -5
  add(2, 3) == 6 (WRONG - that's multiplication!)

subtract/subtraction:
  subtract(5, 3) == 2
  subtract(0, 5) == -5
  subtract(-2, -3) == 1

multiply/multiplication:
  multiply(2, 3) == 6
  multiply(0, 5) == 0
  multiply(-2, 3) == -6

divide/diviser/division:
  divide(10, 2) == 5.0
  divide(9, 2) == 4.5
  diviser(10, 2) == 5.0
  divide(10, 0) raises ZeroDivisionError
  divide(10, 2) == 20 (WRONG!)

calculate_average/get_average/mean:
  calculate_average([10, 20]) == 15.0 (sum/length)
  calculate_average([1, 2, 3]) == 2.0
  calculate_average([]) raises ValueError or returns None
  calculate_average([10, 20]) == 30.0 (WRONG - that's sum, not average!)

validate_email/check_email/is_valid_email:
  validate_email("test@example.com") == True
  validate_email("invalid") == False
  validate_email("no-at-sign.com") == False

sort_list/sort_array:
  sort_list([3, 1, 2]) == [1, 2, 3]
  sort_list([]) == []

═══════════════════════════════════════════════════════════════════
TEST COVERAGE REQUIREMENTS (ALL FUNCTIONS)
═══════════════════════════════════════════════════════════════════

For EVERY function, include:

1. NORMAL CASES (typical valid inputs):
   - Basic functionality test
   - Common use cases

2. EDGE CASES:
   - Empty inputs ([], "", None, 0)
   - Negative numbers (if applicable)
   - Zero values
   - Large numbers
   - Boundary conditions

3. ERROR CASES:
   - Invalid types (string when expecting int)
   - Invalid values (division by zero)
   - None values
   - Exceptions that should be raised

═══════════════════════════════════════════════════════════════════
EXAMPLES OF CORRECT TESTS
═══════════════════════════════════════════════════════════════════

Category A - SEMANTIC (strict expectations):
```python
def test_add_normal_case():
    \"\"\"Test add returns sum of two numbers.\"\"\"
    assert {module_name}.add(2, 3) == 5  # MUST be 5, not 6!

def test_add_with_zero():
    \"\"\"Test add with zero.\"\"\"
    assert {module_name}.add(0, 5) == 5

def test_add_negative_numbers():
    \"\"\"Test add with negative numbers.\"\"\"
    assert {module_name}.add(-2, 3) == 1

def test_divide_normal():
    \"\"\"Test division returns correct quotient.\"\"\"
    assert {module_name}.diviser(10, 2) == 5.0

def test_divide_by_zero():
    \"\"\"Test division by zero raises error.\"\"\"
    with pytest.raises(ZeroDivisionError):
        {module_name}.diviser(10, 0)
```

Category B - CUSTOM (implementation + edge cases):
```python
def test_custom_function_normal():
    \"\"\"Test custom function with valid input.\"\"\"
    result = {module_name}.custom_function(valid_input)
    assert result is not None
    assert isinstance(result, expected_type)

def test_custom_function_edge_empty():
    \"\"\"Test custom function handles empty input.\"\"\"
    result = {module_name}.custom_function([])
    # Test based on actual implementation behavior

def test_custom_function_error():
    \"\"\"Test custom function with invalid type.\"\"\"
    with pytest.raises(TypeError):
        {module_name}.custom_function("invalid")
```

═══════════════════════════════════════════════════════════════════
WRONG EXAMPLES (NEVER DO THIS)
═══════════════════════════════════════════════════════════════════

assert {module_name}.add(2, 3) == 6  # Wrong! add should return 5
assert {module_name}.add(0, 5) == 0  # Wrong! 0 + 5 = 5
assert {module_name}.calculate_average([10, 20]) == 30.0  # Wrong! That's sum
assert {module_name}.divide(10, 2) == 20  # Wrong! 10 / 2 = 5.0

═══════════════════════════════════════════════════════════════════
PYTHON CODE TO TEST
═══════════════════════════════════════════════════════════════════

{code}

MODULE NAME: {module_name}
FILE PATH: {code_path}

═══════════════════════════════════════════════════════════════════
IMPORT AND EXECUTION INSTRUCTIONS
═══════════════════════════════════════════════════════════════════

- Use: import {module_name}
- If code has "if __name__ == '__main__'", test only the functions
- DO NOT use input() or print() in tests
- DO NOT execute the main block
- Each test must be independent and self-contained

═══════════════════════════════════════════════════════════════════
GENERATION RULES
═══════════════════════════════════════════════════════════════════

1. Classify each function (Category A or B)
2. For Category A: Use STRICT semantic expectations
3. For Category B: Test implementation + edge cases
4. Include normal, edge, and error cases for ALL functions
5. Use descriptive test names and docstrings
6. Return ONLY Python code (no ```python```, no markdown, no explanations)

CRITICAL REMINDER:
- Semantic functions (add, divide, etc.) MUST follow semantic meaning
- If a function named "add" does multiplication, the test SHOULD FAIL
- This is CORRECT behavior - it helps detect bugs!
- Expected: add(2, 3) == 5, Got: 6 → TEST FAILS (Bug detected!)

GENERATED SEMANTIC TEST CODE (Python only, no markdown):
"""
        
        try:
            response = self.llm.invoke(prompt)
            test_code = response.content
            # Nettoyer le code généré pour pytest - Clean generated code for pytest
            test_code = test_code.replace("```python", "").replace("```", "").strip()
            
            # Vérifier que le code contient au moins une fonction test_ - Ensure code contains at least one test_ function -
            if "def test_" not in test_code:
                raise ValueError("Generated code doesn't contain test functions")
            
            log_experiment(
             agent_name="JudgeAgent",
             model_used="llama-3.3-70b-versatile",
             action=ActionType.GENERATION,
             details={
                "file_analyzed": str(code_path),
                "module_name": module_name,
                "input_prompt": prompt,
                "output_response": test_code,
                "tests_detected": len([line for line in test_code.splitlines() if line.strip().startswith("def test_")])
             },
             status="SUCCESS"
        )
            
            return test_code
            
        except Exception as e:
            if self.verbose:
                print(f"  LLM test generation failed: {e}, using fallback")
            return "def test_dummy():\n    assert True"


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
                "output_response": f"Passed: {result['pytest_passed']}, Score: {result['pylint_score']}",
                "pytest_passed": result.get("pytest_passed", False),
                "pylint_score": result.get("pylint_score"),
                "tests_generated": result.get("tests_generated", False),
                "errors": result.get("errors", []),
                "pytest_output_preview": result.get("pytest_output", "")[:500]
            },
            status=status
        )

    def _analyze_failures(self, code: str, pytest_output: str = None, pylint_output: str = None, pylint_score: float = None) -> dict:
        """
        Analyse les échecs de tests et les problèmes de Pylint.
        Retourne un JSON compatible avec le FixerAgent.
        """
        # Construire le prompt pour l'agent LLM d'analyse combinée - Build prompt for combined analysis LLM agent
        prompt_parts = []
        if pytest_output:
            prompt_parts.append(f"## PYTEST OUTPUT:\n{pytest_output}")
        if pylint_output:
            prompt_parts.append(f"## PYLINT OUTPUT:\n{pylint_output}\nScore: {pylint_score}")
        prompt = f"""
ROLE: Python Test & Code Analyzer Expert
TASK: Analyze pytest failures and Pylint issues, producing a refactoring plan compatible with the FixerAgent.
OUTPUT: STRICT JSON only.
## ABSOLUTE RULES (VERY IMPORTANT):
- DO NOT use ```json
- DO NOT use ```
- DO NOT wrap the output in markdown
- DO NOT add explanations or comments
- Output must start with {{ and end with }}
## MANDATORY OUTPUT FORMAT:
{{
  "issues_found": integer,
  "refactoring_plan": [
    {{
      "priority": "CRITICAL|HIGH|MEDIUM",
      "category": "IMPORT_ERROR|INPUT_BLOCKING|MAIN_EXECUTION|ASSERTION_FAILURE|CONVENTION|REFACTORING",
      "issue": "brief description",
      "line": integer,
      "code_snippet": "pytest or pylint relevant code",
      "suggestion": "specific fix needed"
    }}
  ],
  "pylint_score": {pylint_score if pylint_score is not None else 0.0},
  "summary": "one sentence summary"
}}
## RULES:
- Each pytest failure MUST generate exactly ONE refactoring_plan entry
- Each Pylint issue MUST generate exactly ONE refactoring_plan entry
- line = 0 if exact line is unknown
- code_snippet must come from pytest or pylint output
- suggestion must describe an explicit code change
- DO NOT invent problems
## CODE BEING TESTED:
{code}
## OUTPUT TO ANALYZE:
{chr(10).join(prompt_parts)}
## YOUR RESPONSE (PURE JSON ONLY):
"""
        try:
            response = self.llm.invoke(prompt)
            import json
            result = json.loads(response.content.strip())
            if self.verbose:
                print(f"\n Analyse combinée: {result.get('issues_found', 0)} issues trouvées .")

            log_experiment(
            agent_name="JudgeAgent",
            model_used="llama-3.3-70b-versatile",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": prompt,
                "output_response": response.content,
                "issues_detected": len(result.get("refactoring_plan", []))
            },
            status="SUCCESS"
        )
            return result
        except Exception as e:
            if self.verbose:
                print(f"Erreur lors de l'analyse: {e}")
            # Fallback compatible FixerAgent
            fallback_code_snippet = ""
            if pytest_output:
                fallback_code_snippet += pytest_output[:200]
            if pylint_output:
                fallback_code_snippet += "\n" + pylint_output[:200]
            return {
                "issues_found": 1,
                "refactoring_plan": [
                    {
                        "priority": "CRITICAL",
                        "category": "ASSERTION_FAILURE" if pytest_output else "REFACTORING",
                        "issue": "Judge analysis failed",
                        "line": 0,
                        "code_snippet": fallback_code_snippet,
                        "suggestion": "Inspect outputs manually"
                    }
                ],
                "pylint_score": pylint_score if pylint_score is not None else 0.0,
                "summary": "Judge failed to analyze outputs"
            }