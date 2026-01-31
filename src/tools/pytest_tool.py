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


    return {
        "passed": passed,
        "output": output,
                }
