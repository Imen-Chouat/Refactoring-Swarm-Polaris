import json
import re
from typing import Dict, Any
from pathlib import Path


class PromptManager:
    def __init__(self):
        # getting all availbe propmts
        base_dir = Path(__file__).resolve().parent
        self.prompts_directory = base_dir

        self.prompts_list = self._load_prompts()

        #some restructions :  Gemini-safe limits
        self.max_chars = 12000
        self.code_buffer = 2000
        

    def _load_prompts(self) -> Dict[str, str]:
        prompts = {} # list of all prompt files
        if not self.prompts_directory.exists():#ensuring that the prompt directory exists
            raise FileNotFoundError(
                f"Prompt directory not found: {self.prompts_directory}"
            )

        for file in self.prompts_directory.glob("*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                prompts[file.stem] = f.read() # Remove .txt extension

        return prompts


    def get_auditor_prompt(self, code_snippet: str, version: str = "v2") -> str:
        prompt_key = f"auditor_{version}"

        if prompt_key not in self.prompts_list:
            raise ValueError(f"Prompt '{prompt_key}' not found in {self.prompts_directory}")

        base_prompt = self.prompts_list[prompt_key]

        if "{code_snippet}" not in base_prompt:
            raise ValueError("Prompt template missing {code_snippet} placeholder.")

        base_chars = len(base_prompt)
        available_for_code = self.max_chars - base_chars - self.code_buffer

        if available_for_code <= 0:
            raise ValueError("Base prompt too large for Gemini context window.")

        if len(code_snippet) > available_for_code:
            print("Code too long — trimming due to Gemini restruction")
            code_snippet = self._trim_code(code_snippet, available_for_code)

        final_prompt = base_prompt.replace("{code_snippet}", code_snippet)

        if len(final_prompt) > self.max_chars:
            print("Prompt close to Gemini context limit")

        return final_prompt


    def _trim_code(self, code: str, max_chars: int) -> str:
        lines = code.splitlines()
        kept = []
        current = 0

        for line in lines:
            line_len = len(line) + 1
            if current + line_len > max_chars:
                break
            kept.append(line)
            current += line_len

        if len(kept) < 10 and len(lines) > 10:
            kept = (
                lines[:5]
                + ["# ... [code trimmed for Gemini analysis] ..."]
                + lines[-5:]
            )

        return "\n".join(kept)

    
    def validate_json_output(self, output: str) -> Dict[str, Any]:
        output = output.strip()
        output = re.sub(r"^```(?:json)?", "", output)
        output = re.sub(r"```$", "", output)
        output = output.strip()

        try:
            data = json.loads(output)
            self._validate_schema(data)
            return data
        except json.JSONDecodeError:
            pass

        matches = re.findall(r"\{[\s\S]*?\}", output)
        for match in sorted(matches, key=len, reverse=True):
            try:
                data = json.loads(match)
                self._validate_schema(data)
                return data
            except json.JSONDecodeError:
                continue

        raise ValueError("Invalid or missing JSON in Gemini output.")

    # --------------------------------------------------
    def _validate_schema(self, data: Dict[str, Any]) -> None:
        required = {"issues_found", "refactoring_plan", "summary", "pylint_score"}

        missing = required - data.keys()
        if missing:
            raise ValueError(f"Missing JSON keys: {missing}")

        if not isinstance(data["refactoring_plan"], list):
            raise ValueError("refactoring_plan must be a list")

        for item in data["refactoring_plan"]:
            if not isinstance(item, dict):
                raise ValueError("Each refactoring_plan item must be a dict")
