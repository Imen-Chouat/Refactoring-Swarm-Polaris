"""
Judge Agent v2 - Minimal output, clear failure summaries.
"""
import subprocess
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import tempfile
import os

from src.llm_client import call_llm
from src.prompts.prompt_manager import PromptManager
from src.utils.logger import log_experiment, ActionType
from src.utils.config import DEFAULT_MODEL, TEST_TIMEOUT


class JudgeAgent:
    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = False):
        self.model = model
        self.verbose = verbose
        self.prompt_manager = PromptManager()
    
    def evaluate_code(self, code: str, file_path: Optional[Path] = None, 
                     iteration: int = 1) -> Dict[str, Any]:
        """
        Evaluate code quality and provide pass/fail verdict.
        Returns JSON with minimal, clear output.
        """
        if self.verbose:
            print(f"Judge agent: (iteration {iteration})...")
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Run tests and get pylint score
            test_results = self._run_tests(temp_file)
            pylint_score = self._run_pylint(temp_file)
            
            # Determine verdict
            verdict = self._determine_verdict(test_results, pylint_score)
            
            # Create failure summary if needed
            failure_summary = ""
            if verdict["status"] == "FAIL":
                failure_summary = self._create_failure_summary(test_results, pylint_score)
            
            # Determine next action
            next_action = self._determine_next_action(verdict["status"], iteration)
            
            # Build result
            result = {
                "status": verdict["status"],
                "tests_passed": test_results["passed"],
                "tests_failed": test_results["failed"],
                "pylint_score": round(pylint_score, 2),
                "critical_issues_remaining": verdict["critical_issues"],
                "failure_summary": failure_summary,
                "next_action": next_action,
                "iteration": iteration
            }
            
            # Log evaluation
            self._log_evaluation(result, code, file_path)
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "FAIL",
                "tests_passed": 0,
                "tests_failed": 1,
                "pylint_score": 0.0,
                "critical_issues_remaining": 1,
                "failure_summary": f"Evaluation error: {str(e)[:50]}",
                "next_action": "RETRY" if iteration < 10 else "ABORT",
                "iteration": iteration
            }
            
            self._log_evaluation(error_result, code, file_path, error=str(e))
            return error_result
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _run_tests(self, file_path: str) -> Dict[str, Any]:
        """Run pytest on the file with timeout"""
        try:
            # First check for syntax errors
            compile_result = subprocess.run(
                [sys.executable, "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if compile_result.returncode != 0:
                return {
                    "passed": 0,
                    "failed": 1,
                    "test_names": ["syntax_check"],
                    "errors": [compile_result.stderr[:200]]
                }
            
            # Run pytest
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, "-m", "pytest", file_path, "-v"],
                capture_output=True,
                text=True,
                timeout=TEST_TIMEOUT
            )
            
            # Parse pytest output
            passed = 0
            failed = 0
            test_names = []
            
            for line in result.stdout.split('\n'):
                if "PASSED" in line:
                    passed += 1
                    test_name = line.split('::')[-1].split()[0]
                    test_names.append(f"PASS:{test_name}")
                elif "FAILED" in line or "ERROR" in line:
                    failed += 1
                    test_name = line.split('::')[-1].split()[0]
                    test_names.append(f"FAIL:{test_name}")
            
            return {
                "passed": passed,
                "failed": failed,
                "test_names": test_names,
                "stdout": result.stdout[-500:],  # Last 500 chars
                "stderr": result.stderr[-200:],  # Last 200 chars
                "time": time.time() - start_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "failed": 1,
                "test_names": ["timeout"],
                "errors": [f"Tests timed out after {TEST_TIMEOUT}s"],
                "time": TEST_TIMEOUT
            }
        except Exception as e:
            return {
                "passed": 0,
                "failed": 1,
                "test_names": ["execution"],
                "errors": [str(e)[:100]],
                "time": 0
            }
    
    def _run_pylint(self, file_path: str) -> float:
        """Run pylint and extract score"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pylint", "--exit-zero", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Extract score from output
            for line in result.stdout.split('\n'):
                if "Your code has been rated at" in line:
                    # Format: "Your code has been rated at 8.50/10"
                    score_text = line.split("at")[1].split("/")[0].strip()
                    try:
                        return float(score_text)
                    except:
                        pass
            
            # If no score found, estimate from return code
            return 5.0 if result.returncode == 0 else 3.0
            
        except Exception:
            return 5.0  # Default score
    
    def _determine_verdict(self, test_results: Dict[str, Any], pylint_score: float) -> Dict[str, Any]:
        """Determine PASS/FAIL verdict"""
        # Check for critical issues
        critical_issues = 0
        
        if test_results["failed"] > 0:
            # Check if failures are critical
            for test in test_results.get("test_names", []):
                if "FAIL:" in test or "ERROR" in test:
                    critical_issues += 1
        
        # Determine status
        if test_results["failed"] == 0 and pylint_score >= 8.0:
            status = "PASS"
        else:
            status = "FAIL"
        
        return {
            "status": status,
            "critical_issues": critical_issues
        }
    
    def _create_failure_summary(self, test_results: Dict[str, Any], pylint_score: float) -> str:
        """Create a clear, concise failure summary"""
        reasons = []
        
        # Test failures
        if test_results["failed"] > 0:
            failed_tests = [t for t in test_results.get("test_names", []) if "FAIL:" in t]
            if failed_tests:
                test_names = ", ".join([t.replace("FAIL:", "") for t in failed_tests[:3]])
                if len(failed_tests) > 3:
                    test_names += f" and {len(failed_tests) - 3} more"
                reasons.append(f"{test_results['failed']} tests failed: {test_names}")
            else:
                reasons.append(f"{test_results['failed']} tests failed")
        
        # Pylint score
        if pylint_score < 8.0:
            reasons.append(f"Quality score {pylint_score:.1f}/10 below threshold")
        
        # Timeout
        if test_results.get("test_names", []) and "timeout" in test_results["test_names"]:
            reasons.append("Tests timed out")
        
        # Syntax errors
        if "syntax_check" in test_results.get("test_names", []):
            errors = test_results.get("errors", [])
            if errors:
                reasons.append(f"Syntax error: {errors[0][:50]}")
        
        # Join with semicolons, limit length
        summary = "; ".join(reasons)[:150]  # Max 150 chars
        
        # Ensure it's not empty
        if not summary:
            summary = "Unknown failure"
        
        return summary
    
    def _determine_next_action(self, status: str, iteration: int) -> str:
        """Determine what to do next based on status and iteration"""
        if status == "PASS":
            return "STOP"
        elif iteration >= 10:
            return "ABORT"
        else:
            return "RETRY"
    
    def _log_evaluation(self, result: Dict[str, Any], code: str, 
                       file_path: Optional[Path], error: str = ""):
        """Log the evaluation result"""
        details = {
            "status": result["status"],
            "tests_passed": result["tests_passed"],
            "tests_failed": result["tests_failed"],
            "pylint_score": result["pylint_score"],
            "failure_summary": result["failure_summary"],
            "next_action": result["next_action"],
            "iteration": result["iteration"]
        }
        
        if error:
            details["error"] = error
        
        if file_path:
            details["file_evaluated"] = str(file_path)
        
        log_experiment(
            agent_name="judge",
            model_used=self.model,
            action=ActionType.ANALYSIS if result["status"] == "PASS" else ActionType.DEBUG,
            details={
                "input_prompt": f"Evaluate code quality iteration {result['iteration']}",
                "output_response": json.dumps(result),
                **details
            },
            status="SUCCESS" if not error else "ERROR"
        )
    
    def quick_evaluate(self, code: str) -> bool:
        """Quick evaluation without full logging (for internal use)"""
        try:
            # Simple syntax check
            compile(code, '<string>', 'exec')
            
            # Quick pylint-like check
            lines = code.split('\n')
            issues = 0
            
            # Basic checks
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Check for obvious issues
                if len(line) > 120:  # Too long
                    issues += 0.1
                if stripped.startswith('except:') or stripped.startswith('except :'):  # Bare except
                    issues += 1
                if 'eval(' in line or 'exec(' in line:  # Dangerous
                    issues += 2
            
            # Approximate score (10 - issues, min 0)
            score = max(0, 10 - issues)
            
            return score >= 8.0
            
        except SyntaxError:
            return False