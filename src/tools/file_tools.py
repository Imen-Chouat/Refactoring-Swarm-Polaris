from pathlib import Path

SANDBOX_DIR = Path("sandbox").resolve()

def _check_sandbox(path: Path):
    if not str(path.resolve()).startswith(str(SANDBOX_DIR)):
        raise PermissionError("Accés en dehors le sandbox n'est pas autorisé") 
    


def read_file(file_path: str) -> str:
    path = Path(file_path)
    _check_sandbox(path)
    return path.read_text(encoding="utf-8")


def write_file(file_path: str, content: str):
    path = Path(file_path)
    _check_sandbox(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")