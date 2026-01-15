from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.file_tools import read_file


class FixerAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash",
            temperature=0
        )

        with open("src/prompts/fixer_prompt_v1.txt", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def fix_file(self, file_path: Path, refactoring_plan: list):
        if not refactoring_plan:
            return None, []

        code = read_file(str(file_path))

        prompt = f"""
{self.prompt_template}

ORIGINAL FILE:
{code}

REFACTORING PLAN:
{refactoring_plan}
"""

        response = self.llm.invoke(prompt)
        fixed_code = response.content

        return fixed_code, refactoring_plan