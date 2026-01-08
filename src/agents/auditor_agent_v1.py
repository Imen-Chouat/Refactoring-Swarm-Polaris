"""
Auditor Agent with strict JSON output and hallucination prevention.
"""
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.llm_client import call_llm
from src.prompts.prompt_manager import PromptManager
from src.utils.logger import log_experiment, ActionType
from src.utils.config import DEFAULT_MODEL


class AuditorAgent:
    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = False):
        self.model = model
        self.verbose = verbose
        self.prompt_manager = PromptManager()
        self.hallucination_checks = []
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a Python file and return structured refactoring plan.
        """
        if self.verbose:
            print(f"Auditor agent , analyzing file : {file_path.name}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            return self._create_error_response(error_msg)
        
        # Create prompt
        prompt = self.prompt_manager.get_auditor_prompt(code_content, version="v2")
        
        # Log the prompt
        log_experiment(
            agent_name="auditor",
            model_used=self.model,
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": str(file_path),
                "input_prompt": prompt,
                "output_response": "",  # Will be filled after LLM call
                "code_length": len(code_content),
                "lines": len(code_content.split('\n'))
            },
            status="PENDING"
        )
        
        # Call LLM
        try:
            raw_response = call_llm(
                prompt=prompt,
                model_name=self.model,
                temperature=0.1,  # Low temperature for consistency
                max_tokens=1000
            )
            
            if self.verbose:
                print(f"Raw response length: {len(raw_response)} chars")
            
            # Validate and parse JSON
            validated_response = self._validate_and_clean_response(
                raw_response, code_content, str(file_path)
            )
            
            # Log successful analysis
            log_experiment(
                agent_name="auditor",
                model_used=self.model,
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": str(file_path),
                    "input_prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "output_response": json.dumps(validated_response),
                    "issues_found": validated_response.get("issues_found", 0),
                    "pylint_score": validated_response.get("pylint_score", 0),
                    "hallucination_checks": self.hallucination_checks
                },
                status="SUCCESS"
            )
            
            return validated_response
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            if self.verbose:
                print(f"error: {error_msg}")
            
            # Log failure
            log_experiment(
                agent_name="auditor",
                model_used=self.model,
                action=ActionType.DEBUG,
                details={
                    "file_analyzed": str(file_path),
                    "input_prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "output_response": error_msg,
                    "error": str(e)
                },
                status="ERROR"
            )
            
            return self._create_error_response(error_msg)
    
    def _validate_and_clean_response(self, raw_response: str, 
                                    original_code: str, 
                                    file_path: str) -> Dict[str, Any]:
        """
        Validate LLM response and prevent hallucinations.
        """
        # Step 1: Extract JSON from response
        json_data = self.prompt_manager.validate_json_output(raw_response)
        
        # Step 2: Anti-hallucination checks
        self.hallucination_checks = self._check_hallucinations(json_data, original_code)
        
        if self.hallucination_checks:
            if self.verbose:
                print(f"Hallucination checks: {self.hallucination_checks}")
        
        # Step 3: Validate line numbers
        json_data = self._validate_line_numbers(json_data, original_code)
        
        # Step 4: Clean and normalize data
        json_data = self._clean_response_data(json_data)
        
        # Step 5: Add metadata
        json_data["file_name"] = Path(file_path).name
        json_data["analysis_timestamp"] = "2025-01-10T12:00:00Z"  # TODO: Use actual timestamp
        json_data["hallucination_warnings"] = len(self.hallucination_checks)
        
        return json_data
    
    def _check_hallucinations(self, data: Dict[str, Any], original_code: str) -> List[str]:
        """
        Check for common hallucinations in LLM responses.
        """
        warnings = []
        lines = original_code.split('\n')
        
        if "refactoring_plan" in data and isinstance(data["refactoring_plan"], list):
            for item in data["refactoring_plan"]:
                # Check 1: Valid line numbers
                if "line" in item:
                    line_num = item["line"]
                    if isinstance(line_num, int):
                        if line_num < 1 or line_num > len(lines):
                            warnings.append(f"Invalid line number: {line_num}")
                
                # Check 2: Code snippet actually exists
                if "code_snippet" in item:
                    snippet = item["code_snippet"].strip()
                    if snippet and snippet not in original_code:
                        # Check if it's a substring
                        if not any(snippet in line for line in lines):
                            warnings.append(f"Code snippet not found: '{snippet[:50]}...'")
                
                # Check 3: Don't suggest imports that are already present
                if "suggestion" in item and "import" in item["suggestion"].lower():
                    suggestion = item["suggestion"].lower()
                    if "import" in suggestion:
                        # Extract module name
                        import_match = re.search(r'import\s+(\w+)', suggestion)
                        if import_match:
                            module = import_match.group(1)
                            if f"import {module}" in original_code.lower():
                                warnings.append(f"Import already present: {module}")
        
        return warnings
    
    def _validate_line_numbers(self, data: Dict[str, Any], original_code: str) -> Dict[str, Any]:
        """
        Validate and correct line numbers in the refactoring plan.
        """
        lines = original_code.split('\n')
        
        if "refactoring_plan" in data and isinstance(data["refactoring_plan"], list):
            for item in data["refactoring_plan"]:
                if "line" in item and isinstance(item["line"], int):
                    line_num = item["line"]
                    
                    # Ensure line number is within bounds
                    if line_num < 1:
                        item["line"] = 1
                    elif line_num > len(lines):
                        item["line"] = len(lines)
                    
                    # Try to find the actual line if code_snippet is provided
                    if "code_snippet" in item:
                        snippet = item["code_snippet"].strip()
                        if snippet:
                            # Search for the snippet in the code
                            for i, line in enumerate(lines, 1):
                                if snippet in line:
                                    item["line"] = i
                                    break
        
        return data
    
    def _clean_response_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize the response data.
        """
        # Ensure issues_found is integer
        if "issues_found" in data:
            try:
                data["issues_found"] = int(data["issues_found"])
            except:
                data["issues_found"] = 0
        
        # Ensure pylint_score is float between 0-10
        if "pylint_score" in data:
            try:
                score = float(data["pylint_score"])
                data["pylint_score"] = max(0.0, min(10.0, score))
            except:
                data["pylint_score"] = 5.0  # Default
        
        # Clean refactoring plan
        if "refactoring_plan" in data:
            if not isinstance(data["refactoring_plan"], list):
                data["refactoring_plan"] = []
            
            # Remove empty or invalid items
            data["refactoring_plan"] = [
                item for item in data["refactoring_plan"]
                if isinstance(item, dict) and "issue" in item
            ]
        
        # Ensure summary is string
        if "summary" not in data or not isinstance(data["summary"], str):
            data["summary"] = "The Analysis of code is completed"
        
        return data
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "issues_found": 0,
            "refactoring_plan": [],
            "pylint_score": 0.0,
            "summary": error_message,
            "error": True,
            "error_message": error_message
        }