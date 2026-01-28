"""
Outil pytest - Exécute les tests sur un fichier Python
"""

import subprocess
import re
from pathlib import Path


def run_pytest(file_path: str) -> dict:
    """
    Exécute pytest sur un fichier Python donné.
    
    Args:
        file_path: Chemin vers le fichier Python à tester
        
    Returns:
        dict: {
            'passed': bool,  # True si tous les tests passent
            'output': str,   # Sortie complète de pytest
            'pylint_score': float or None  # Score Pylint si disponible
        }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Exécuter pytest
    process = subprocess.run(
        ["pytest", str(path), "--tb=short", "--disable-warnings"],
        capture_output=True,
        text=True
    )

    output = process.stdout + process.stderr
    passed = process.returncode == 0  # 0 = succès dans pytest

    # Essayer d'obtenir le score Pylint en parallèle
    pylint_score = _run_pylint_score(path)

    return {
        "passed": passed,
        "output": output,
        "pylint_score": pylint_score
    }


def _run_pylint_score(file_path: Path) -> float:
    """
    Exécute Pylint et extrait le score.
    Retourne None si Pylint n'est pas disponible ou échoue.
    """
    try:
        process = subprocess.run(
            ["pylint", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = process.stdout + process.stderr
        
        # Extraire le score avec regex
        match = re.search(r"rated at ([\d\.]+)/10", output)
        if match:
            return float(match.group(1))
        
        return None
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None