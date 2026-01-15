"""
Enhanced prompt manager with token optimization and JSON validation.
"""

import json
import tiktoken  # For token counting
from typing import Dict, Any
from pathlib import Path

class PromptManager:
    def __init__(self, prompt_dir: str = "prompts"):
        self.prompt_dir = prompt_dir
        self.prompts = self._load_prompts()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  #  tokenizer
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load all prompt files"""
        prompts = {}
        prompt_path = Path(self.prompt_dir)
        
        if not prompt_path.exists():
            print(f"⚠️ Prompt directory not found: {self.prompt_dir}")
            return prompts
        
        for file in prompt_path.glob("*.txt"):
            with open(file, 'r', encoding='utf-8') as f:
                key = file.stem  # Remove .txt extension
                prompts[key] = f.read()
        
        return prompts
    
    def get_auditor_prompt(self, code_snippet: str, version: str = "v2") -> str:
        """
        Get auditor prompt with injected code snippet.
        Automatically trims code to fit token budget.
        """
        # Load base prompt
        prompt_key = f"auditor_{version}"
        if prompt_key not in self.prompts:
            prompt_key = "auditor_v2"  # Fallback
        
        base_prompt = self.prompts[prompt_key]
        
        # Calculate available tokens
        max_tokens = 3000  # Gemini 1.5-flash limit
        prompt_tokens = self.count_tokens(base_prompt)
        available_for_code = max_tokens - prompt_tokens - 500  # Buffer
        
        # Trim code if too long
        code_tokens = self.count_tokens(code_snippet)
        if code_tokens > available_for_code:
            print(f"⚠️ Code too long ({code_tokens} tokens), trimming...")
            code_snippet = self._trim_code_to_tokens(code_snippet, available_for_code)
        
        # Inject code
        final_prompt = base_prompt.replace("{code_snippet}", code_snippet)
        
        # Verify token count
        total_tokens = self.count_tokens(final_prompt)
        if total_tokens > max_tokens:
            print(f"⚠️ Warning: Prompt exceeds {max_tokens} tokens")
        
        return final_prompt
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def _trim_code_to_tokens(self, code: str, max_tokens: int) -> str:
        """Trim code to fit token budget while preserving structure"""
        lines = code.split('\n')
        trimmed_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line + '\n')
            if current_tokens + line_tokens > max_tokens:
                break
            trimmed_lines.append(line)
            current_tokens += line_tokens
        
        # Always keep first and last few lines for context
        if len(trimmed_lines) < 10 and len(lines) > 10:
            # Keep first 5 and last 5 lines
            trimmed_lines = lines[:5] + ["# ... [code trimmed for analysis] ..."] + lines[-5:]
        
        return '\n'.join(trimmed_lines)
    
    def validate_json_output(self, output: str) -> Dict[str, Any]:
        """
        Validate and clean JSON output from LLM.
        Returns parsed JSON or raises exception.
        """
        # Remove markdown code blocks if present
        if output.startswith('```json'):
            output = output[7:]
        if output.endswith('```'):
            output = output[:-3]
        if output.startswith('```'):
            output = output[3:]
        
        # Clean up common LLM artifacts
        output = output.strip()
        
        # Try to parse JSON
        try:
            data = json.loads(output)
            
            # Validate required structure
            required_keys = ["issues_found", "refactoring_plan", "summary"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Missing required key: {key}")
            
            # Validate refactoring plan format
            if isinstance(data["refactoring_plan"], list):
                for item in data["refactoring_plan"]:
                    if not isinstance(item, dict):
                        raise ValueError("Refactoring plan items must be dicts")
            
            return data
            
        except json.JSONDecodeError as e:
            # Try to extract JSON from text
            import re
            json_pattern = r'\{[\s\S]*?\}'
            matches = re.findall(json_pattern, output, re.DOTALL)
            
            if matches:
                # Try the longest match (most likely the JSON)
                for match in sorted(matches, key=len, reverse=True):
                    try:
                        data = json.loads(match)
                        return data
                    except:
                        continue
            
            raise ValueError(f"Invalid JSON output: {str(e)}")