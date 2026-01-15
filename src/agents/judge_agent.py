from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.pytest_tool import run_pytest
import tempfile

class JudgeAgent:
    ACTION_TYPE = "DEBUG"

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash",
            temperature=0
        )
        self.prompt_path = "src/prompts/judge_prompt_v2.txt"
        self.prompt_text = ""
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                self.prompt_text = f.read()
        except FileNotFoundError:
            self.prompt_text = ""

    def quick_evaluate(self, code: str) -> bool:
        # Write code to temporary file to run pytest
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        result = run_pytest(tmp_file_path)

        if self.verbose:
            print(f"[Judge] {tmp_file_path}: {'PASS' if result['passed'] else 'FAIL'}, Pylint {result.get('pylint_score')}")

        # Cleanup temporary file
        try:
            import os
            os.remove(tmp_file_path)
        except Exception:
            pass

        return result["passed"]