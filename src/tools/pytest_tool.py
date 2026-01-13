import subprocess
from pathlib import Path

def run_pytest(file_path: str) -> dict:
    """
    Runs pytest on a given Python file.
    Returns:
      - 'passed': True if all tests pass, False otherwise
      - 'output': full pytest output
    This is used by the Judge Agent to confirm success or summarize failures.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    process = subprocess.run(
        ["pytest", str(path), "--tb=short", "--disable-warnings"],
        capture_output=True,
        text=True
    )

    output = process.stdout + process.stderr
    passed = process.returncode == 0  # 0 = success in pytest

    return {
        "passed": passed,
        "output": output
    }
