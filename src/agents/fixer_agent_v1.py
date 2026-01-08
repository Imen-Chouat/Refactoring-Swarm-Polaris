"""
Fixer Agent v2 - Applies ONLY specified fixes, prevents feature invention.
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from copy import deepcopy

from src.llm_client import call_llm
from src.prompts.prompt_manager import PromptManager
from src.utils.logger import log_experiment, ActionType
from src.utils.config import DEFAULT_MODEL, BLACKLISTED_IMPORTS


@dataclass
class FixAttempt:
    """Track each fix attempt"""
    issue: Dict[str, Any]
    success: bool
    applied_fix: str
    line_changed: int
    error: str = ""


class FixerAgent:
    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = False):
        self.model = model
        self.verbose = verbose
        self.prompt_manager = PromptManager()
        self.fix_history: List[FixAttempt] = []
    
    def fix_file(self, file_path: Path, refactoring_plan: List[Dict]) -> Tuple[str, List[FixAttempt]]:
        """
        Fix a file using ONLY the specified refactoring plan.
        Returns: (fixed_code, fix_attempts)
        """
        if self.verbose:
            print(f"🔧 Fixer processing: {file_path.name}")
            print(f"   Issues to fix: {len(refactoring_plan)}")
        
        # Read original code
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            log_experiment(
                agent_name="fixer",
                model_used=self.model,
                action=ActionType.FIX,
                details={
                    "file_fixed": str(file_path),
                    "input_prompt": "N/A - File read error",
                    "output_response": error_msg,
                    "error": str(e)
                },
                status="ERROR"
            )
            return original_code, []
        
        # Filter and validate refactoring plan
        validated_plan = self._validate_refactoring_plan(refactoring_plan, original_code)
        
        if self.verbose and len(validated_plan) != len(refactoring_plan):
            print(f"   ⚠️  Filtered {len(refactoring_plan) - len(validated_plan)} invalid issues")
        
        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        validated_plan.sort(key=lambda x: priority_order.get(x.get("priority", "LOW"), 3))
        
        # Create prompt
        prompt = self._create_fixer_prompt(original_code, validated_plan)
        
        # Log before fix
        log_experiment(
            agent_name="fixer",
            model_used=self.model,
            action=ActionType.FIX,
            details={
                "file_fixed": str(file_path),
                "input_prompt": prompt[:1000] + "..." if len(prompt) > 1000 else prompt,
                "output_response": "",  # Will be filled
                "issues_to_fix": len(validated_plan),
                "priority_breakdown": self._count_priorities(validated_plan)
            },
            status="PENDING"
        )
        
        # Call LLM for fixes
        try:
            fixed_code = call_llm(
                prompt=prompt,
                model_name=self.model,
                temperature=0.1,  # Very low for consistency
                max_tokens=len(original_code) + 1000  # Allow for added comments
            )
            
            # Post-process: Ensure it's just code
            fixed_code = self._clean_fixer_output(fixed_code)
            
            # Verify fixes were minimal
            verification = self._verify_fixes(original_code, fixed_code, validated_plan)
            
            # Log results
            log_experiment(
                agent_name="fixer",
                model_used=self.model,
                action=ActionType.FIX,
                details={
                    "file_fixed": str(file_path),
                    "input_prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "output_response": fixed_code[:500] + "..." if len(fixed_code) > 500 else fixed_code,
                    "issues_fixed": len([f for f in self.fix_history if f.success]),
                    "issues_skipped": len([f for f in self.fix_history if not f.success]),
                    "verification_passed": verification["passed"],
                    "verification_issues": verification["issues"]
                },
                status="SUCCESS" if verification["passed"] else "PARTIAL"
            )
            
            return fixed_code, self.fix_history
            
        except Exception as e:
            error_msg = f"Fixer failed: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            log_experiment(
                agent_name="fixer",
                model_used=self.model,
                action=ActionType.DEBUG,
                details={
                    "file_fixed": str(file_path),
                    "input_prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "output_response": error_msg,
                    "error": str(e)
                },
                status="ERROR"
            )
            
            return original_code, []
    
    def _validate_refactoring_plan(self, plan: List[Dict], code: str) -> List[Dict]:
        """Validate refactoring plan and filter out invalid issues"""
        lines = code.split('\n')
        validated = []
        
        for issue in plan:
            # Check required fields
            if not all(key in issue for key in ["issue", "priority", "suggestion"]):
                if self.verbose:
                    print(f"   ⚠️  Skipping issue missing required fields")
                continue
            
            # Validate line number
            line_num = issue.get("line", 0)
            if not isinstance(line_num, int) or line_num < 1 or line_num > len(lines):
                if self.verbose:
                    print(f"   ⚠️  Skipping issue with invalid line {line_num}")
                continue
            
            # Check for blacklisted suggestions
            suggestion = issue.get("suggestion", "").lower()
            if any(blacklisted in suggestion for blacklisted in ["os.system", "eval", "exec", "__import__"]):
                if self.verbose:
                    print(f"   ⚠️  Skipping issue with dangerous suggestion")
                continue
            
            # Verify issue exists at line
            code_snippet = issue.get("code_snippet", "").strip()
            if code_snippet and code_snippet not in lines[line_num - 1]:
                if self.verbose:
                    print(f"   ⚠️  Code snippet doesn't match line {line_num}")
                continue
            
            validated.append(issue)
        
        return validated
    
    def _create_fixer_prompt(self, original_code: str, refactoring_plan: List[Dict]) -> str:
        """Create the fixer prompt with code and plan"""
        # Load base prompt
        base_prompt = self.prompt_manager.prompts_list.get("fixer_v2", "")
        if not base_prompt:
            # Fallback minimal prompt
            base_prompt = """Fix ONLY these issues in the code. Return fixed code only.

CODE:
{original_code}

ISSUES TO FIX:
{refactoring_plan}

FIXED CODE:"""
        
        # Format plan for prompt
        plan_text = json.dumps(refactoring_plan, indent=2)
        
        # Inject into prompt
        prompt = base_prompt.replace("{original_code}", original_code)
        prompt = prompt.replace("{refactoring_plan}", plan_text)
        
        return prompt
    
    def _clean_fixer_output(self, output: str) -> str:
        """Clean LLM output to get just Python code"""
        # Remove markdown code blocks
        if output.startswith('```python'):
            output = output[9:]
        elif output.startswith('```'):
            output = output[3:]
        
        if output.endswith('```'):
            output = output[:-3]
        
        # Remove any JSON or explanations before code
        lines = output.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Skip JSON lines
            if line.strip().startswith('{') or line.strip().startswith('['):
                continue
            # Skip explanation lines
            if line.strip().lower().startswith(('here', 'fixed', 'output', 'result')):
                continue
            
            # Start code at first Python-like line
            if not in_code and any(line.strip().startswith(keyword) 
                                  for keyword in ['import ', 'def ', 'class ', '#']):
                in_code = True
            
            if in_code or line.strip() == '':
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _verify_fixes(self, original: str, fixed: str, plan: List[Dict]) -> Dict[str, Any]:
        """Verify that fixes were minimal and correct"""
        original_lines = original.split('\n')
        fixed_lines = fixed.split('\n')
        
        issues = []
        
        # Check 1: No major additions
        if len(fixed_lines) > len(original_lines) * 1.5:  # 50% more lines max
            issues.append(f"Too many lines added: {len(fixed_lines)} vs {len(original_lines)}")
        
        # Check 2: Critical imports not added
        for line in fixed_lines:
            for blacklisted in BLACKLISTED_IMPORTS:
                if blacklisted in line and blacklisted not in original:
                    issues.append(f"Dangerous import added: {blacklisted}")
        
        # Check 3: Function signatures preserved
        original_funcs = self._extract_function_signatures(original)
        fixed_funcs = self._extract_function_signatures(fixed)
        
        if original_funcs != fixed_funcs:
            issues.append("Function signatures changed")
        
        # Check 4: No new syntax errors
        try:
            compile(fixed, '<string>', 'exec')
        except SyntaxError as e:
            issues.append(f"Syntax error introduced: {str(e)}")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def _extract_function_signatures(self, code: str) -> List[str]:
        """Extract function signatures from code"""
        signatures = []
        lines = code.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                # Get just the def line (stop at colon or comment)
                signature = stripped.split('#')[0].strip()
                signatures.append(signature)
        
        return signatures
    
    def _count_priorities(self, plan: List[Dict]) -> Dict[str, int]:
        """Count issues by priority"""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in plan:
            priority = issue.get("priority", "LOW")
            if priority in counts:
                counts[priority] += 1
        return counts