import subprocess
import re
from pathlib import Path

def run_pylint(file_path: str) -> dict:
    """
    Runs pylint on a given Python file.
    Returns a dictionary with:
      - 'output': full pylint text output
      - 'score': float score (0-10) if found, else None
    This is used by the Auditor Agent to detect style/logic violations.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    process = subprocess.run(
        ["pylint", str(path)],
        capture_output=True,
        text=True
    )

    output = process.stdout + process.stderr

    # Extract score from pylint
    score = None
    match = re.search(r"rated at ([\d\.]+)/10", output)
    if match:
        score = float(match.group(1))

    return {
        "output": output,
        "score": score
    }
